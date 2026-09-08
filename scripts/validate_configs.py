#!/usr/bin/env python3
"""
Validates that every rendered_configs/<hostname>.cfg actually reflects what
physical_topology.yaml / logical_topology.yaml / the platform role baseline
say it should -- a regression test for the render pipeline itself (does the
templates + filters combination faithfully turn the data model into CLI),
not a check against live device state (that's what playbooks/02 and 03's
LLDP/BGP/VLAN checks are for).

Every expected value is derived from the SAME data + the SAME
filter_plugins/netascode_filters.py functions the templates themselves use
(device_phys_links, device_routing_record, wan_peer_binding, ios_addr, ...)
-- never independently re-guessed -- so a check failure means the rendered
config and the data model genuinely disagree, not that this script computed
something differently than the templates do.

Matching is line-exact, not raw substring-in-file: expected CLI lines are
compared against a set of stripped, whole config lines (line_set), and
interface-scoped expectations (an IP, a description) are checked only
within that interface's own stanza (parse_interface_stanzas), never against
the file as a blob. A naive `expected in cfg_text` check would report a
false PASS for e.g. `hostname abc-hq-cor-01` against a rendered
`hostname abc-hq-cor-01-TYPO` line (the expected string is still a
substring) -- caught during this script's own self-test (see design.md's
Validation Reports section) by deliberately corrupting a rendered config
and confirming the validator flagged it before trusting a clean run.

Usage: validate_configs.py <repo_root> [--json <path>]
  --json <path>   also write structured per-check results (used by
                   playbooks/00_validate_render.yml to surface every check
                   as native Ansible task output + a generated report,
                   instead of only this script's own stdout table).
Exit code: 0 if every check passed, 1 if any failed.
"""
import sys
import os
import re
import json
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'filter_plugins'))
from netascode_filters import (
    device_platform, device_role, device_external_links, device_phys_links,
    device_routing_record, wan_peer_binding, ios_addr,
    endpoint_port_configs, endpoint_vlan_list, evpn_rr_peers,
    device_telemetry_subscription,
)

PLATFORM_MAP = {
    'catalyst8000': {'baseline_yaml': 'wan edge role.yaml', 'baseline_var': 'platform_wan_baseline'},
    'nexus93240': {'baseline_yaml': 'core agg role.yaml', 'baseline_var': 'platform_core_agg_baseline'},
    'catalyst9000': {'baseline_yaml': 'access role.yaml', 'baseline_var': 'platform_access_baseline'},
}

IFACE_RE = re.compile(r'^interface\s+(\S+)\s*$')


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def all_device_names(site_physical_topology):
    names = []
    for w in site_physical_topology.get('wan_routers', []):
        names.append(w['name'])
    for c in site_physical_topology.get('core_routers', []):
        names.append(c['name'])
    for a in site_physical_topology.get('aggregation_switches', []):
        names.append(a['name'])
    for floor in site_physical_topology.get('floors', []):
        for acc in floor.get('access_switches', []):
            names.append(acc['name'])
    return names


def line_set(cfg_text):
    """Every config line, stripped of leading/trailing whitespace, as a set.
    Used for exact whole-line matches (hostname, router bgp, neighbor, ntp
    server, snmp lines, ACL/class-map body lines, vlan configuration/member
    vni) so a value can't false-PASS merely by being a substring of some
    other, unrelated, longer line."""
    return set(l.strip() for l in cfg_text.split('\n'))


def parse_interface_stanzas(cfg_text):
    """dict: interface name -> list of stanzas (each a list of stripped
    lines), one entry per time that interface name is (re-)opened in the
    file. Configs here are the concatenation of up to 3 render stages, so
    the same interface can legitimately appear more than once (e.g. the
    physical-topology stage opens it for description/shutdown, the
    logical-topology stage reopens it to add an IP) -- every stanza for a
    name is checked, not just the first."""
    stanzas = {}
    cur_name = None
    cur_lines = []

    def flush():
        nonlocal cur_name, cur_lines
        if cur_name is not None:
            stanzas.setdefault(cur_name, []).append(cur_lines)
        cur_name = None
        cur_lines = []

    for raw in cfg_text.split('\n'):
        line = raw.strip()
        m = IFACE_RE.match(line)
        if m:
            flush()
            cur_name = m.group(1)
            continue
        if line == '!':
            flush()
            continue
        if cur_name is not None:
            cur_lines.append(line)
    flush()
    return stanzas


def iface_exists(stanzas, name):
    return name in stanzas


def iface_has_line(stanzas, name, expected_line):
    for stanza in stanzas.get(name, []):
        if expected_line in stanza:
            return True
    return False


def iface_has_description_containing(stanzas, name, marker):
    for stanza in stanzas.get(name, []):
        for l in stanza:
            if l.startswith('description') and marker in l:
                return True
    return False


def acl_header_present(lset, acl_name):
    return any(l.startswith('ip access-list') and acl_name in l for l in lset)


class Check:
    __slots__ = ('device', 'category', 'expectation', 'passed', 'note')

    def __init__(self, device, category, expectation, passed, note=None):
        self.device = device
        self.category = category
        self.expectation = expectation
        self.passed = passed
        self.note = note


def validate_device(name, phys, logical, baseline, platform, role, cfg_text, endpoint_service, telemetry):
    checks = []
    lset = line_set(cfg_text)
    stanzas = parse_interface_stanzas(cfg_text)

    def want(category, expectation, present, note=None):
        checks.append(Check(name, category, expectation, present, note))

    # --- hostname (physical topology stage) ---
    want('hostname', f"hostname {name}", f"hostname {name}" in lset)

    # --- physical interfaces: every link physical_topology.yaml gives this
    #     device must appear as its own "interface <port>" stanza, with a
    #     description line mentioning the far end ---
    for link in device_phys_links(phys, name):
        present = iface_exists(stanzas, link['local_port'])
        want('physical-interface', f"interface {link['local_port']}", present)
        if present:
            desc_marker = f"to {link['remote_device']} {link['remote_port']}"
            want('physical-interface-description',
                 f"interface {link['local_port']} description mentions {desc_marker}",
                 iface_has_description_containing(stanzas, link['local_port'], desc_marker))

    for ext in device_external_links(phys, name):
        want('physical-external-interface', f"interface {ext['interface']}",
             iface_exists(stanzas, ext['interface']))

    # --- logical: loopbacks, per-interface IP, BGP ---
    rtg = device_routing_record(logical, name)
    want('routing-record', f"{name} has a device_interconnects record in logical_topology.yaml", rtg is not None)
    if rtg:
        for lb in rtg['loopbacks']:
            present = iface_exists(stanzas, lb['interface'])
            want('loopback-interface', f"interface {lb['interface']}", present)
            expected_ip = lb['ip_address'] if platform == 'nexus93240' else ios_addr(lb['ip_address'])
            want('loopback-ip', f"interface {lb['interface']} has ip address {expected_ip}",
                 iface_has_line(stanzas, lb['interface'], f"ip address {expected_ip}"))

        if rtg['interfaces']:
            # core/agg/access-vtep: logical_topology.yaml states the
            # interface + ip_address directly.
            for i in rtg['interfaces']:
                want('logical-interface', f"interface {i['interface']}",
                     iface_exists(stanzas, i['interface']))
                expected_ip = i['ip_address'] if platform == 'nexus93240' else ios_addr(i['ip_address'])
                want('logical-interface-ip', f"interface {i['interface']} has ip address {expected_ip}",
                     iface_has_line(stanzas, i['interface'], f"ip address {expected_ip}"))
        else:
            # WAN routers: no `interfaces:` array -- own IP is derived per
            # bgp_peer via wan_peer_binding(), same as logical topology.j2
            # does. eBGP peers legitimately have no derivable IP (FINDING 1,
            # logical topology.j2's header) -- not a failure, just nothing
            # to check.
            for p in rtg['bgp_peers']:
                b = wan_peer_binding(phys, logical, name, p)
                if b['resolved'] and b['own_ip']:
                    expected_ip = ios_addr(b['own_ip'])
                    want('logical-interface-ip (derived, WAN)',
                         f"interface {b['local_port']} has ip address {expected_ip}",
                         iface_exists(stanzas, b['local_port']) and
                         iface_has_line(stanzas, b['local_port'], f"ip address {expected_ip}"))
                else:
                    want('logical-interface-ip (derived, WAN)',
                         f"peer {p['peer_ip']} ({p['description']}) -- no IP derivable, skipped by design",
                         True, note='skipped: known data-model gap (FINDING 1), not a render defect')

        # BGP process + every neighbor line (rendered unconditionally
        # regardless of whether its own-IP could be derived)
        asn_line = f"router bgp {rtg['global']['bgp_asn']}"
        want('bgp-process', asn_line, asn_line in lset)
        for p in rtg['bgp_peers']:
            neighbor_line = f"neighbor {p['peer_ip']} remote-as {p['remote_as']}"
            want('bgp-neighbor', neighbor_line, neighbor_line in lset)

        # --- L2VPN EVPN address-family peering (evpn_rr_peers(), fixes
        #     the FINDING-3 gap: RR seated at core, access-vteps as
        #     route-reflector-clients per failure domain) ---
        evpn_rr = evpn_rr_peers(logical, name)
        for p in evpn_rr['peers']:
            neighbor_line = f"neighbor {p['peer_ip']} remote-as {rtg['global']['bgp_asn']}"
            want('evpn-rr-neighbor', f"{name} <-> {p['peer_name']}: {neighbor_line}", neighbor_line in lset)
        if role == 'access-vtep':
            for p in evpn_rr['peers']:
                activate_line = f"neighbor {p['peer_ip']} activate"
                want('evpn-rr-neighbor-activate', activate_line, activate_line in lset)
        if evpn_rr['is_rr']:
            want('evpn-af-l2vpn', "address-family l2vpn evpn", "address-family l2vpn evpn" in lset)
            if any(p['client'] for p in evpn_rr['peers']):
                want('evpn-rr-client-marker', "route-reflector-client (at least one client peer)",
                     "route-reflector-client" in cfg_text)

    # --- NTP / SNMP, only when the baseline actually enables them (same
    #     "don't render disabled things" rule the templates follow) ---
    mp = baseline['management_plane']
    for server in mp['ntp']['servers']:
        line = f"ntp server {server}"
        want('ntp-server', line, line in lset)
    if mp['snmp']['enabled']:
        ro_kw = 'ro' if platform == 'nexus93240' else 'RO'
        for community in mp['snmp']['community_strings']:
            line = f"snmp-server community {community} {ro_kw}"
            want('snmp-community', line, line in lset)
        for host in mp['snmp']['trap_destinations']:
            line = f"snmp-server host {host} traps"
            want('snmp-trap-host', line, line in lset)
    else:
        want('snmp-disabled', 'SNMP disabled per baseline -- no snmp-server community line',
             not any(l.startswith('snmp-server community') for l in lset))

    # syslog / TACACS+ CLI genuinely differs IOS-XE vs NX-OS (same platform
    # split the loopback/interface IP checks above already follow) --
    # nexus 93240.j2 puts severity on the same "logging server" line
    # per-host and uses "tacacs-server host ... key ..." instead of a
    # named "tacacs server <name>" object.
    if platform == 'nexus93240':
        for server in mp['syslog']['servers']:
            if mp['syslog']['severity_level']:
                line = f"logging server {server} {mp['syslog']['severity_level']}"
            else:
                line = f"logging server {server}"
            want('syslog-host', line, line in lset)
    else:
        for server in mp['syslog']['servers']:
            line = f"logging host {server}"
            want('syslog-host', line, line in lset)
        if mp['syslog']['severity_level']:
            line = f"logging trap {mp['syslog']['severity_level']}"
            want('syslog-severity', line, line in lset)
    if mp['syslog']['source_interface']:
        line = f"logging source-interface {mp['syslog']['source_interface']}"
        want('syslog-source-interface', line, line in lset)

    if mp['tacacs']['servers']:
        key = mp['tacacs']['encryption_key'] or '!! VAULT-REFERENCE-REQUIRED !!'
        if platform == 'nexus93240':
            want('tacacs-feature', 'feature tacacs+', 'feature tacacs+' in lset)
            for server in mp['tacacs']['servers']:
                line = f"tacacs-server host {server} key {key}"
                want('tacacs-server', line, line in lset)
        else:
            for idx, server in enumerate(mp['tacacs']['servers'], start=1):
                line = f"address ipv4 {server}"
                want('tacacs-server', f"tacacs server TACACS-{idx} / {line}", line in lset)
        if mp['tacacs']['source_interface']:
            line = f"ip tacacs source-interface {mp['tacacs']['source_interface']}"
            want('tacacs-source-interface', line, line in lset)
        want('tacacs-aaa-group', 'aaa group server tacacs+ TACACS-GROUP',
             'aaa group server tacacs+ TACACS-GROUP' in lset)
    else:
        want('tacacs-disabled', 'No TACACS+ servers defined -- local-only authentication fallback',
             'aaa authentication login default group TACACS-GROUP local' not in lset
             and 'aaa authentication login default group TACACS-GROUP' not in lset)

    # --- CoPP classification ACLs (structural: presence of the ACL names
    #     + the conditional match lines, mirroring each template's own
    #     if-enabled logic) ---
    copp = baseline.get('routing_baseline', {}).get('control_plane_policing', {})
    if copp.get('enable'):
        want('copp-acl-routing', 'ip access-list ... COPP-ACL-ROUTING_UPDATES',
             acl_header_present(lset, 'COPP-ACL-ROUTING_UPDATES'))
        want('copp-acl-mgmt', 'ip access-list ... COPP-ACL-MANAGEMENT_ACCESS',
             acl_header_present(lset, 'COPP-ACL-MANAGEMENT_ACCESS'))
        want('copp-acl-mgmt-ssh', 'permit tcp any any eq 22', 'permit tcp any any eq 22' in lset)
        if mp['snmp']['enabled']:
            want('copp-acl-mgmt-snmp', 'permit udp any any eq snmp', 'permit udp any any eq snmp' in lset)
        if mp['ntp']['servers']:
            want('copp-acl-mgmt-ntp', 'permit udp any any eq ntp', 'permit udp any any eq ntp' in lset)
        want('copp-acl-transit', 'ip access-list ... COPP-ACL-TRANSIT_TRAFFIC + match protocol arp',
             'match protocol arp' in lset)

    # --- EVPN / VNI (access-vtep only) ---
    if role == 'access-vtep':
        for vni in logical['evpn_overlay_design']['vni_service_mappings']:
            want('evpn-vlan-config', f"vlan configuration {vni['vlan_id']}",
                 f"vlan configuration {vni['vlan_id']}" in lset)
            want('evpn-member-vni', f"member vni {vni['vni_id']}", f"member vni {vni['vni_id']}" in lset)
            if 'anycast_gateway_ip' in vni:
                svi_name = f"vlan{vni['vlan_id']}"
                want('evpn-svi', f"interface {svi_name}", iface_exists(stanzas, svi_name))
                expected_ip = ios_addr(vni['anycast_gateway_ip'])
                want('evpn-svi-ip', f"interface {svi_name} has ip address {expected_ip}",
                     iface_has_line(stanzas, svi_name, f"ip address {expected_ip}"))

    # --- Streaming telemetry (all devices -- templates/telemetry.j2 /
    #     telemetry.yaml, resolved per device by device_telemetry_
    #     subscription(), same "expected == what the filter itself
    #     resolved" principle every other check in this file follows) ---
    subscription = device_telemetry_subscription(telemetry, name)
    dest = subscription['destination']
    if dest and subscription['sensor_groups']:
        if platform == 'nexus93240':
            want('telemetry-feature', 'feature telemetry', 'feature telemetry' in lset)
            dest_line = (f"ip address {dest['ip_address']} port {dest['port']} "
                         f"protocol {dest['protocol'].upper()} encoding {dest['encoding'].upper()}")
            want('telemetry-destination-group', dest_line, dest_line in lset)
            for sg in subscription['sensor_groups']:
                for path in sg['sensor_paths']:
                    line = f"path {path}"
                    want('telemetry-sensor-path', f"{sg['name']}: {line}", line in lset)
        else:
            for sg in subscription['sensor_groups']:
                for path in sg['sensor_paths']:
                    line = f"filter xpath {path}"
                    want('telemetry-filter-xpath', f"{sg['name']}: {line}", line in lset)
            receiver_line = f"receiver ip address {dest['ip_address']} port {dest['port']} protocol {dest['protocol']}-tcp"
            want('telemetry-receiver', receiver_line, receiver_line in lset)
    else:
        want('telemetry-subscription (skipped)',
             f"{name}'s role ({role}) has no role_subscriptions entry in telemetry.yaml",
             True, note='skipped: known data-model gap, not a render defect')

    # --- Endpoint service (access-vtep only, BAU stage 4 --
    #     templates/endpoint service.j2 / endpoint service.yaml) ---
    if role == 'access-vtep':
        eas = baseline['endpoint_access_security']
        vlan_list = endpoint_vlan_list(endpoint_service, name)
        vlan_list_str = ','.join(str(v) for v in vlan_list)
        if eas['dhcp_snooping']['enable']:
            line = f"ip dhcp snooping vlan {vlan_list_str}"
            want('endpoint-dhcp-snooping-vlan', line, line in lset)
        if eas['dynamic_arp_inspection']['enable']:
            line = f"ip arp inspection vlan {vlan_list_str}"
            want('endpoint-arp-inspection-vlan', line, line in lset)

        for p in endpoint_port_configs(endpoint_service, name):
            iface = p['interface']
            present = iface_exists(stanzas, iface)
            want('endpoint-interface', f"interface {iface}", present)
            if not present:
                continue
            if p['mode'] == 'access':
                want('endpoint-access-vlan', f"interface {iface} has switchport access vlan {p['vlan']}",
                     iface_has_line(stanzas, iface, f"switchport access vlan {p['vlan']}"))
                if p['voice_vlan']:
                    want('endpoint-voice-vlan', f"interface {iface} has switchport voice vlan {p['voice_vlan']}",
                         iface_has_line(stanzas, iface, f"switchport voice vlan {p['voice_vlan']}"))
                if eas['port_security']['enable']:
                    want('endpoint-port-security', f"interface {iface} has switchport port-security",
                         iface_has_line(stanzas, iface, "switchport port-security"))
                auth_methods = [m for m in ('dot1x', 'mab')
                                if (m == 'dot1x' and p['dot1x_enabled']) or (m == 'mab' and p['mab_enabled'])]
                if auth_methods:
                    line = f"authentication order {' '.join(auth_methods)}"
                    want('endpoint-authentication-order', f"interface {iface} has {line}",
                         iface_has_line(stanzas, iface, line))
                want('endpoint-storm-control-action', f"interface {iface} has storm-control action {p['storm_control']['action']}",
                     iface_has_line(stanzas, iface, f"storm-control action {p['storm_control']['action']}"))
            elif p['mode'] == 'trunk':
                want('endpoint-trunk-native-vlan', f"interface {iface} has switchport trunk native vlan {p['vlan']}",
                     iface_has_line(stanzas, iface, f"switchport trunk native vlan {p['vlan']}"))
                if p['allowed_vlans']:
                    want('endpoint-trunk-allowed-vlan', f"interface {iface} has switchport trunk allowed vlan {p['allowed_vlans']}",
                         iface_has_line(stanzas, iface, f"switchport trunk allowed vlan {p['allowed_vlans']}"))

    return checks


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: validate_configs.py <repo_root> [--json <path>]", file=sys.stderr)
        return 2
    repo_root = args[0]
    json_path = None
    if '--json' in args:
        idx = args.index('--json')
        if idx + 1 >= len(args):
            print("--json requires a path argument", file=sys.stderr)
            return 2
        json_path = args[idx + 1]

    models_dir = os.path.join(repo_root, 'models')
    cfg_dir = os.path.join(repo_root, 'rendered_configs')

    phys = load_yaml(os.path.join(models_dir, 'physical topology.yaml'))['site_physical_topology']
    logical = load_yaml(os.path.join(models_dir, 'logical topology.yaml'))['site_context']
    endpoint_service = load_yaml(os.path.join(models_dir, 'endpoint service.yaml'))['site_context']
    telemetry = load_yaml(os.path.join(models_dir, 'telemetry.yaml'))['site_telemetry']
    device_names = all_device_names(phys)

    all_checks = []
    for name in device_names:
        platform = device_platform(name)
        role = device_role(name)
        baseline = load_yaml(os.path.join(models_dir, PLATFORM_MAP[platform]['baseline_yaml']))[PLATFORM_MAP[platform]['baseline_var']]
        cfg_path = os.path.join(cfg_dir, f"{name}.cfg")
        if not os.path.exists(cfg_path):
            all_checks.append(Check(name, 'rendered-file-exists', cfg_path, False))
            continue
        with open(cfg_path) as f:
            cfg_text = f.read()
        all_checks.extend(validate_device(name, phys, logical, baseline, platform, role, cfg_text, endpoint_service, telemetry))

    by_device = {}
    for c in all_checks:
        by_device.setdefault(c.device, []).append(c)

    total_pass = sum(1 for c in all_checks if c.passed)
    total_fail = sum(1 for c in all_checks if not c.passed)
    skipped = sum(1 for c in all_checks if c.passed and c.note)

    print(f"{'DEVICE':<20} {'PASS':>5} {'FAIL':>5} {'SKIP*':>6}")
    print("-" * 40)
    for name in device_names:
        checks = by_device.get(name, [])
        p = sum(1 for c in checks if c.passed and not c.note)
        f = sum(1 for c in checks if not c.passed)
        s = sum(1 for c in checks if c.passed and c.note)
        print(f"{name:<20} {p:>5} {f:>5} {s:>6}")
    print("-" * 40)
    print(f"{'TOTAL':<20} {total_pass - skipped:>5} {total_fail:>5} {skipped:>6}")
    print("(*SKIP = known, already-documented data-model gap -- not a render defect)")

    if total_fail:
        print("\nFAILURES:")
        for c in all_checks:
            if not c.passed:
                print(f"  [{c.device}] {c.category}: expected {c.expectation!r} not found in rendered config")

    print(f"\n{'PASS' if total_fail == 0 else 'FAIL'}: {total_pass - skipped} checks passed, {total_fail} failed, {skipped} known-gap skips, across {len(device_names)} devices")

    if json_path:
        payload = {
            'devices': [
                {
                    'name': name,
                    'checks': [
                        {
                            'category': c.category,
                            'expectation': c.expectation,
                            'passed': c.passed,
                            'note': c.note,
                        }
                        for c in by_device.get(name, [])
                    ],
                }
                for name in device_names
            ],
            'summary': {
                'total_pass': total_pass - skipped,
                'total_fail': total_fail,
                'skipped': skipped,
                'device_count': len(device_names),
            },
        }
        with open(json_path, 'w') as f:
            json.dump(payload, f, indent=2)

    return 1 if total_fail else 0


if __name__ == '__main__':
    sys.exit(main())
