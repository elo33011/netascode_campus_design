"""
NetAsCode-style Jinja2 filter plugins for the campus design's physical /
logical topology deployment templates.

These mirror what would normally ship as an Ansible `filter_plugins/`
module in this repo: physical_topology.yaml and logical_topology.yaml are
passed into the Jinja2 render context as-is (same convention the existing
platform baseline templates use -- they reference platform_wan_baseline.*
directly), and these filters do the per-device lookups a `template` task
looped over `inventory_hostname` would need.
"""
import ipaddress
import re


# ---------------------------------------------------------------------------
# Platform / role mapping (from design.md "Device Role Models" table:
# WAN Edge Role -> Catalyst 8000, Core & Agg Role -> Nexus 93240,
# Access Role -> Catalyst 9000). Neither yaml model carries a platform
# field, so this mapping is derived from the device-naming convention
# (-wan-, -cor-, -agg-, -acc-) established consistently across both
# physical_topology.yaml and logical_topology.yaml.
# ---------------------------------------------------------------------------
def device_platform(name):
    if '-wan-' in name:
        return 'catalyst8000'
    if '-cor-' in name:
        return 'nexus93240'
    if '-agg-' in name:
        return 'nexus93240'
    if '-acc-' in name:
        return 'catalyst9000'
    return 'unknown'


def device_role(name):
    if '-wan-' in name:
        return 'wan-edge'
    if '-cor-' in name:
        return 'core'
    if '-agg-' in name:
        return 'aggregation-transit'
    if '-acc-' in name:
        return 'access-vtep'
    return 'unknown'


# ---------------------------------------------------------------------------
# Physical topology helpers
# ---------------------------------------------------------------------------
def _phys_tier_lists(site_physical_topology):
    """(device_list, link_field_name) for every tier, including per-floor
    access switches. wan_routers' external_links are handled separately
    (they don't connect to another campus device)."""
    root = site_physical_topology
    yield root.get('wan_routers', []), 'internal_links'
    yield root.get('core_routers', []), 'links'
    yield root.get('aggregation_switches', []), 'links'
    for floor in root.get('floors', []):
        yield floor.get('access_switches', []), 'uplinks'


def device_external_links(site_physical_topology, name):
    for w in site_physical_topology.get('wan_routers', []):
        if w['name'] == name:
            return w.get('external_links', [])
    return []


def device_phys_links(site_physical_topology, name):
    """Bidirectional physical link list for one device.

    physical_topology.yaml is inconsistent about which side declares a
    link: same-tier horizontal links (WAN<->WAN, Core<->Core, Agg<->Agg)
    are declared from BOTH endpoints, but cross-tier links (WAN<->Core,
    Core<->Agg, Agg<->Access) are declared from only ONE endpoint (e.g.
    core_routers declares the Core<->Agg link; aggregation_switches does
    not restate it). Keying the result by local_port -- forward (this
    device's own declared entries) taking priority, reverse (some other
    device's entry naming this device as remote_device) only filling in
    ports not already covered -- handles both cases without double-
    rendering the symmetrically-declared links.
    """
    by_port = {}
    for devlist, key in _phys_tier_lists(site_physical_topology):
        for d in devlist:
            if d['name'] != name:
                continue
            for l in d.get(key, []):
                by_port[l['local_port']] = {
                    'local_port': l['local_port'],
                    'remote_device': l['remote_device'],
                    'remote_port': l['remote_port'],
                    'link_type': l['type'],
                    'direction': 'declared-here',
                }
    for devlist, key in _phys_tier_lists(site_physical_topology):
        for d in devlist:
            if d['name'] == name:
                continue
            for l in d.get(key, []):
                if l['remote_device'] == name and l['remote_port'] not in by_port:
                    by_port[l['remote_port']] = {
                        'local_port': l['remote_port'],
                        'remote_device': d['name'],
                        'remote_port': l['local_port'],
                        'link_type': l['type'],
                        'direction': 'declared-remotely',
                    }
    return list(by_port.values())


# ---------------------------------------------------------------------------
# Logical topology helpers
# ---------------------------------------------------------------------------
def _logical_tier_lists(site_context):
    dic = site_context['device_interconnects']
    yield dic.get('wan_routers', []), 'routing'
    yield dic.get('core_routers', []), 'routing'
    yield dic.get('aggregation_switches', []), 'routing'
    for floor in dic.get('floors', []):
        yield floor.get('access_vteps', []), 'evpn_vtep'


def device_routing_record(site_context, name):
    """Returns a normalised dict: {failure_domain, role, kind, global,
    loopbacks, interfaces, bgp_peers} regardless of whether the source was
    a routing: block (wan/core/agg) or an evpn_vtep: block (access)."""
    for devlist, key in _logical_tier_lists(site_context):
        for d in devlist:
            if d['name'] == name:
                block = d[key]
                return {
                    'failure_domain': d.get('failure_domain'),
                    'role': d.get('role'),
                    'kind': 'access-vtep' if key == 'evpn_vtep' else 'underlay-only',
                    'global': block.get('global', {}),
                    'loopbacks': block.get('loopbacks', []),
                    'interfaces': block.get('interfaces', []),
                    'bgp_peers': block.get('bgp_peers', []),
                }
    return None


def pair31(ip_str):
    """Given one address of an RFC 3021 /31 point-to-point subnet, return
    the other (peer) address as a plain dotted-quad string."""
    ip = ipaddress.ip_address(ip_str)
    net = ipaddress.ip_network(f"{ip_str}/31", strict=False)
    a, b = net.network_address, net.broadcast_address
    return str(b) if ip == a else str(a)


def find_ip_owner(site_context, ip_addr):
    """Search every device's logical-topology `interfaces:` list for one
    matching ip_addr (host part only, ignores prefix) and return that
    device's name, or None. Used to resolve which physical link a WAN
    router's bgp_peers entry (peer_ip only, no interface field) actually
    rides over, without parsing the free-text `description` field."""
    for devlist, key in _logical_tier_lists(site_context):
        for d in devlist:
            block = d.get(key, {})
            for iface in block.get('interfaces', []):
                addr = iface['ip_address'].split('/')[0]
                if addr == ip_addr:
                    return d['name']
    return None


def wan_peer_binding(site_physical_topology, site_context, device_name, peer):
    """For one bgp_peers entry on a WAN router (which has no `interfaces:`
    array of its own in logical_topology.yaml -- see design.md's own
    catalyst 8000.j2 header note), resolve:
      - local_port : the physical interface this session rides over
      - own_ip     : this device's own /31 address on that link
      - resolved   : False if either lookup came up empty (rendered as a
                      NOTE instead of guessed CLI)
    eBGP peers ride the external ISP circuit (assumed 1:1, true for both
    WAN routers in this dataset); iBGP peers are matched by finding which
    other device's logical-topology `interfaces:` entry owns peer_ip, then
    finding the physical link between this device and that device.
    """
    if peer['type'] == 'ebgp':
        ext = device_external_links(site_physical_topology, device_name)
        local_port = ext[0]['interface'] if ext else None
        return {
            'local_port': local_port,
            'own_ip': None,  # not present anywhere in either data model
            'resolved': local_port is not None,
        }
    remote_device = find_ip_owner(site_context, peer['peer_ip'])
    if not remote_device:
        return {'local_port': None, 'own_ip': None, 'resolved': False}
    local_port = None
    for l in device_phys_links(site_physical_topology, device_name):
        if l['remote_device'] == remote_device and l['link_type'] == 'inter_device':
            local_port = l['local_port']
            break
    if not local_port:
        return {'local_port': None, 'own_ip': None, 'resolved': False}
    return {
        'local_port': local_port,
        'own_ip': pair31(peer['peer_ip']) + '/31',
        'resolved': True,
    }


# ---------------------------------------------------------------------------
# Endpoint service (models/endpoint service.yaml) helpers -- BAU switchport
# provisioning. Unlike physical/logical topology (device identity, one-time
# fabric build), this model describes a device-class-wide interface policy
# (endpoint_interfaces.default_profile applied across an interface_range,
# with per-port endpoint_interfaces.port_overrides) that gets re-applied
# any time an endpoint port needs adding/changing -- so these helpers
# expand that policy into one concrete, fully-merged dict per physical
# port, the same "resolve once here, never re-derive in the template"
# principle device_phys_links()/device_routing_record() already follow.
# ---------------------------------------------------------------------------
_IFACE_RANGE_RE = re.compile(r'^(?P<prefix>.*?)(?P<start>\d+)-(?P<end>\d+)$')


def expand_interface_range(range_str):
    """'GigabitEthernet1/0/1-48' -> ['GigabitEthernet1/0/1', ..., 'GigabitEthernet1/0/48'].
    Only the trailing '<start>-<end>' is expanded; everything before it
    (slot/subslot path) is kept as a literal prefix."""
    m = _IFACE_RANGE_RE.match(range_str)
    if not m:
        return [range_str]
    prefix = m.group('prefix')
    start, end = int(m.group('start')), int(m.group('end'))
    return [f"{prefix}{n}" for n in range(start, end + 1)]


def _select_override(candidates, device_name):
    """Given every port_overrides entry for one interface name, pick the
    one that actually applies to this device: an entry whose `switch`
    field matches device_name exactly wins over a switch-agnostic entry
    (switch null/absent, meaning "every access switch"); a switch-scoped
    entry for a DIFFERENT switch never applies here at all. Returns {} if
    nothing matches (this port uses the plain default_profile)."""
    device_match = None
    universal = None
    for o in candidates:
        sw = o.get('switch')
        if sw and sw == device_name:
            device_match = o
        elif not sw:
            universal = o
    return device_match or universal or {}


def _port_vlan_fields(profile_mode, native_vlan, voice_vlan, override):
    """Resolve the effective access/native VLAN + voice VLAN + (trunk)
    allowed VLANs for one port, reconciling the two VLAN-field spellings
    endpoint_service.yaml itself uses: endpoint_interfaces.default_profile
    calls the field 'native_vlan' regardless of mode, while
    port_overrides entries call the same access-mode concept
    'access_vlan' instead (see the GigabitEthernet1/0/1 camera override).
    Both are honoured here rather than picking one and silently dropping
    values written under the other name."""
    mode = override.get('mode', profile_mode)
    if 'access_vlan' in override:
        vlan = override['access_vlan']
    elif 'native_vlan' in override:
        vlan = override['native_vlan']
    else:
        vlan = native_vlan
    if 'voice_vlan' in override:
        voice = override['voice_vlan']
    else:
        voice = voice_vlan
    allowed_vlans = override.get('allowed_vlans')
    return mode, vlan, voice, allowed_vlans


def endpoint_port_configs(endpoint_service, device_name=None):
    """One fully-merged dict per physical port in
    endpoint_interfaces.default_profile.interface_range, with any matching
    endpoint_interfaces.port_overrides entry layered on top. Port-level
    dot1x/mab/vlan fields come from the override when present, else the
    default_profile / authentication_profile; switch-wide fields
    (storm_control, first_hop_security, quality_of_service trust
    settings) are the same for every port -- this model has no per-port
    override for those.

    port_overrides entries are scoped by an optional `switch` field (see
    that key's own comment in endpoint service.yaml): more than one entry
    can share the same `interface` name -- one universal (switch
    null/absent) and/or one for a specific device_name -- and
    _select_override() picks whichever one actually applies to THIS
    device. device_name=None (the historical call signature, still used
    where no specific device is in scope) only ever matches universal
    entries, same as before this field existed."""
    ei = endpoint_service['endpoint_interfaces']
    dp = ei['default_profile']
    ap = ei['authentication_profile']
    fhs = ei['first_hop_security']
    qos = ei['quality_of_service']
    overrides_by_iface = {}
    for o in ei.get('port_overrides', []):
        overrides_by_iface.setdefault(o['interface'], []).append(o)

    ports = []
    for iface in expand_interface_range(dp['interface_range']):
        override = _select_override(overrides_by_iface.get(iface, []), device_name)
        mode, vlan, voice_vlan, allowed_vlans = _port_vlan_fields(
            dp['mode'], dp['native_vlan'], dp['voice_vlan'], override)
        st_default = endpoint_service['interface_provisioning']['access_switch_baseline']['spanning_tree']
        st_override = override.get('spanning_tree', {})
        ports.append({
            'interface': iface,
            'description': override.get('description'),
            'mode': mode,
            'vlan': vlan,
            'voice_vlan': voice_vlan,
            'allowed_vlans': allowed_vlans,
            'administrative_state': dp['administrative_state'],
            'dot1x_enabled': override.get('dot1x_enabled', ap['dot1x_enabled']),
            'mab_enabled': override.get('mab_enabled', ap['mac_authentication_bypass']),
            'host_mode': ap['host_mode'],
            'auth_order': ap['auth_order'],
            'reauth_timer': ap['reauthentication_timer_seconds'],
            'inactivity_timer': ap['inactivity_timer_seconds'],
            'fallback_targets': ap['fallback_targets'],
            'portfast': st_override.get('portfast', st_default['portfast']),
            'bpdu_guard': st_override.get('bpdu_guard', st_default['bpdu_guard']),
            'dhcp_snooping_trust': fhs['dhcp_snooping']['trust'],
            'dhcp_snooping_rate_limit': fhs['dhcp_snooping']['rate_limit_pps'],
            'ip_source_guard': fhs['ip_source_guard'],
            'dai_inspect': fhs['dai_inspect'],
            'storm_control': qos['storm_control'],
            'voice_vlan_trust': qos['voice_vlan_trust'],
            'ingress_policy_map': qos['ingress_policy_map'],
        })
    return ports


def endpoint_vlan_list(endpoint_service, device_name=None):
    """Every VLAN ID this device's own rendered ports reference (default
    profile's native/voice VLAN, its dot1x fallback targets, and any
    port_overrides' native/access/voice/allowed VLANs that apply to
    device_name) -- used for the switch-wide "ip dhcp snooping vlan
    <list>" / "ip arp inspection vlan <list>" commands
    platform_access_baseline's endpoint_access_security block defers
    ("needs the site's VLAN list", not available at the baseline stage)."""
    vlans = set()
    for p in endpoint_port_configs(endpoint_service, device_name):
        if p['vlan'] is not None:
            vlans.add(int(p['vlan']))
        if p['voice_vlan'] is not None:
            vlans.add(int(p['voice_vlan']))
        if p['allowed_vlans']:
            for v in str(p['allowed_vlans']).split(','):
                vlans.add(int(v.strip()))
        for v in p['fallback_targets'].values():
            vlans.add(int(v))
    return sorted(vlans)


def to_netmask(prefixlen):
    return str(ipaddress.IPv4Network(f'0.0.0.0/{int(prefixlen)}').netmask)


def ios_addr(cidr):
    """'10.0.0.1/32' -> '10.0.0.1 255.255.255.255' (classic IOS/IOS-XE
    'ip address' syntax has never accepted CIDR notation)."""
    ip, plen = cidr.split('/')
    return f"{ip} {to_netmask(plen)}"


def evpn_rr_peers(site_context, device_name):
    """L2VPN EVPN address-family neighbors for one device, derived from
    which core_routers carry evpn_route_reflector: true in logical_
    topology.yaml -- the design owner sets that one flag per core; this
    filter derives who actually peers with whom from it, the same
    resolve-once-here principle device_phys_links()/wan_peer_binding()
    already follow (fixes the gap templates/logical topology.j2 used to
    flag as FINDING 3 -- no EVPN overlay peer was ever defined).

    - Each RR-flagged core peers, as a full iBGP EVPN mesh, with every
      OTHER RR-flagged core (so routes reflected in one failure domain
      reach the others) and acts as route-reflector-client toward every
      access-vtep in its OWN failure domain.
    - Each access-vtep peers, as a route-reflector-client, with every
      RR-flagged core in its OWN failure domain -- matching the dual-
      homed redundancy pattern used everywhere else in this design.
    - Every session rides Loopback0 (already used for BGP router-id);
      peers are reached across the underlay, not a direct physical link.

    Returns {'is_rr': bool, 'peers': [{'peer_name', 'peer_ip', 'client'}]}.
    'client' is True only when this device is the RR side of an RR<->
    access-vtep session (renders 'route-reflector-client' there).
    """
    dic = site_context['device_interconnects']
    cores = dic.get('core_routers', [])
    rr_cores = [c for c in cores if c.get('routing', {}).get('evpn_route_reflector')]

    def loopback0(block):
        for lb in block.get('loopbacks', []):
            if lb.get('type') == 'management':
                return lb['ip_address'].split('/')[0]
        return None

    device, kind = None, None
    for c in cores:
        if c['name'] == device_name:
            device, kind = c, 'core'
            break
    if device is None:
        for floor in dic.get('floors', []):
            for a in floor.get('access_vteps', []):
                if a['name'] == device_name:
                    device, kind = a, 'access'
                    break

    if device is None:
        return {'is_rr': False, 'peers': []}

    if kind == 'core' and device.get('routing', {}).get('evpn_route_reflector'):
        peers = []
        for other in rr_cores:
            if other['name'] != device_name:
                peers.append({'peer_name': other['name'],
                               'peer_ip': loopback0(other['routing']),
                               'client': False})
        for floor in dic.get('floors', []):
            for a in floor.get('access_vteps', []):
                if a.get('failure_domain') == device.get('failure_domain'):
                    peers.append({'peer_name': a['name'],
                                  'peer_ip': loopback0(a['evpn_vtep']),
                                  'client': True})
        return {'is_rr': True, 'peers': peers}

    if kind == 'access':
        peers = [{'peer_name': rr['name'], 'peer_ip': loopback0(rr['routing']), 'client': False}
                 for rr in rr_cores if rr.get('failure_domain') == device.get('failure_domain')]
        return {'is_rr': False, 'peers': peers}

    return {'is_rr': False, 'peers': []}


def resolve_rd(rd_template, loopback_cidr):
    """logical_topology.yaml documents route_distinguisher as
    '10.3.0.x:10' where 'x = last octet of the originating access-VTEP's
    Loopback0'. Substitutes that literal 'x' using the device's own
    Loopback0 CIDR string."""
    last_octet = loopback_cidr.split('/')[0].split('.')[-1]
    return rd_template.replace('x', last_octet)


FILTERS = {
    'device_platform': device_platform,
    'device_role': device_role,
    'device_external_links': device_external_links,
    'device_phys_links': device_phys_links,
    'device_routing_record': device_routing_record,
    'pair31': pair31,
    'find_ip_owner': find_ip_owner,
    'wan_peer_binding': wan_peer_binding,
    'expand_interface_range': expand_interface_range,
    'endpoint_port_configs': endpoint_port_configs,
    'endpoint_vlan_list': endpoint_vlan_list,
    'to_netmask': to_netmask,
    'ios_addr': ios_addr,
    'resolve_rd': resolve_rd,
    'evpn_rr_peers': evpn_rr_peers,
}


# ---------------------------------------------------------------------------
# Ansible filter plugin interface. This file doubles as a real Ansible
# `filter_plugins/` module (Ansible auto-discovers a FilterModule class in
# any file under a filter_plugins/ directory next to the playbook -- see
# ansible.cfg's filter_plugins path) AND as the filter set
# scripts/render_configs.py imports directly for the non-Ansible render
# path. Same functions, same behaviour, both callers -- no drift between
# "how the demo script renders a device" and "how the real Ansible
# playbooks render the same device".
# ---------------------------------------------------------------------------
class FilterModule(object):
    def filters(self):
        return FILTERS
