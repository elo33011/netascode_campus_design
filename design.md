# Automation Native Network Design Explain

This is a sample enterprise network design to demonstrate how an automation native network design should look like. Automation native design approach incorporates the following elements required by network automation into the classic design process.

- **Determinsitic Topology**: One repeatable pattern, applied consistently everywhere it occurs
- **Abstraction**: Devices generalized into reusable roles, not configured one by one
- **Machine-Friendly interfaces & structured data**: Intent captured as schema-validated data, not prose or diagrams
- **Unique source of truth**: Each fact lives in exactly one place, never restated elsewhere.
- **Declarative state**: State the desired end result; automation works out the steps
- **Streaming Telemetry**: Live device state flows back continuously, not checked on demand

## Difference between traditional and automation native network design approach

Both approaches pass through the same stages — the difference is *how* each stage is done.

## Key takeaways:
- Data model first, design content generated from various data model.
- Generated contents includes diagrams, cable patching matrix, design specific templates, configurations, playbooks.
- Data model is constructed from various schema by merging the values obtained from source of truth (i.e Netbox). The integration of SOT is not shown in this example.
- Device configuration is render using jinja2 templates by looking up the data models. Ansible comes afterward to deploy.
- Design is validated by comparing the config output with the data model.
- To support BAU port changes, the data model need to be constantly updated to reflect the latest switch port configuration.
- Concept:
  - schema + value = data model
  - data model + template = rendered config
  - playbook + rendered config = deployed config
  - validation = data model vs deployed config

<div style="display: flex; gap: 20px;">
  <div style="flex: 1;">
    <h3>Automation Native Design Approach</h3>
  </div>

  <div style="flex: 1;">
    <img src="diagram/automation-native-data-model-pipeline.svg" width="1200">
  </div>
</div>

---

# Campus Network Design

## Business Requirement

Company ABC is setting up a new 2,000 user campus across a 10-floor building. At this scale, the business needs the network to onboard new starters, moves, and floor-capacity changes quickly without service risk; to keep voice, data, wireless, and fixed-function devices like cameras and IPTV appropriately segmented so a change in one domain can't degrade or expose another. The business also wants these changes itself to be fast, low-risk, and auditable — every BAU change traceable to a reviewed, versioned intent rather than an ad hoc CLI session.

The business requirements can be summarized as:
1. Onboard starters, moves, and floor-capacity changes quickly, without service risk
2. Segment voice/data/wireless/camera/IPTV so one domain can't degrade or expose another
3. BAU Change is fast, low-risk, and auditable

## Technical Requirement

| Business Requirements | Technical Requirements | 
|---|---|
| Onboard starters, moves, and floor-capacity changes quickly, without service risk | ​- A layer 3 Routed Access EVPN-VXLAN Fabric as underlay where Layer 2 / 3 services can be running on top <br> - ​Zero-Trust Access Ports (Identity-Driven Access) |
| Segment voice/data/wireless/camera/IPTV so one domain can't degrade or expose another | - ​Macro-Segmentation (VRF Isolation) to separate differnt business nature of devices into different tenants <br> - ​Micro-Segmentation & QoS Policies to restrict communication between devices within the same tenant |
| BAU Change is fast, low-risk, and auditable | ​- Single Source of Truth (SSoT) & Infrastructure-as-Code (IaC) <br> - ​CI/CD Pipeline with Automated Validation <br> - ​Streaming Telemetry & Closed-Loop Auditing |

## Scope

For the sake of demonstration, the implementation details of management and WIFI network are not covered.

## Network Design

This section outlines the architectural framework and design principles for the campus network:

### Topology & Connectivity Hierarchy

* Implements a standard five-tier architecture: Regional On-Prem/Cloud Colo Access $\rightarrow$ WAN $\rightarrow$ Core $\rightarrow$ Aggregation $\rightarrow$ Access.
* Extends dual-homed connections across all network tiers for end-to-end path redundancy.

![Campus Network Diagram](./diagram/physical.svg)

![Campus Management Network Diagram](./diagram/mgmt_topology.svg)

### Control Plane & Overlay Architecture

* Deploys a unified BGP Routing-based transport underlay.
* Runs EVPN-VXLAN on top of the underlay to deliver flexible Layer 2/Layer 3 multi-tenant virtual overlay networks.
* Seats the L2VPN EVPN route reflector at the Core tier — each access-VTEP peers as a route-reflector-client to the two core routers in its own failure domain; the four RR cores full-mesh each other so routes reflected in one failure domain reach the other.

![Logical Network Diagram](./diagram/logical.svg)

### Network Services & Security

* Mandates 802.1X Network Access Control (NAC) across all Access switch endpoint interfaces.
* Centralizes RADIUS authentication and authorization services within the hub data center.

### Platform Standardization

* WAN Tier: Standardized on a dedicated WAN routing platform optimized for edge peering and WAN features.
* Core & Aggregation Tiers: Standardized on a single, high-throughput campus fabric switching platform.
* Access Tier: Standardized on a dedicated edge-switching platform designed for high-density endpoint connectivity and 802.1X enforcement.

### Resiliency & Fault Isolation

* Enforces complete two-way physical and logical diversity across all infrastructure components (dual WAN routers, dual ISP/colo circuits).
* Extends two-way isolation into dedicated dual failure domains (FD-A and FD-B) spanning the Core, Aggregation, and Access layers.

### Bandwidth & Interface Capacity

* Endpoint Ports: Supports 1Gbps or 10Gbps access connectivity per endpoint interface.
* Inter-Device Trunking: All internal backbone, Core, Aggregation, and inter-plane links operate at 100Gbps.
* WAN Edge Uplinks: Dual 10Gbps dedicated circuits connecting the campus WAN edge to regional on-prem data centers and cloud colocation facilities.

## Data Models

This design is constructed from a set of data models which provides a structure for the "source of truth" information required by the design. The data model is embedded with the value so that it can be used by the automation to render, deploy and validate the configurations. Every data modelis governed by a JSON Schema under [`schemas/`](schemas/) 

### Design Driven Models

Design driven models are specific models created for this design. They defines the physical and logical network topology, as well as the endpoint service (i.e. interface configurations) required on the access switches.

![Model Relationship](./diagram/data-model-relationships.svg)

[Physical Topology - Campus Network](models/physical%20topology.yaml) 

Purpose: Ground-truth inventory of campus network hardware and cabling — devices, ports, and interconnects

- Layer 1/2 only — devices and cabling, no IPs/routing
- Two failure domains (FD-A/FD-B), each a full WAN→Core→Agg stack, cross-connected for domain-level resilience
- Every access switch dual-homed to two different agg switches
- Cross-tier links declared once, reconciled by a filter function (not raw YAML)
- No LACP — each fabric link goes to a different neighbor, ECMP is the redundancy mechanism
- Platform/role derived from hostname, not stored as a field
- OOB management network modeled as a separate, parallel file
- Schema: [physical-topology.schema.json](schemas/physical-topology.schema.json)

[Logical Topology](models/logical%20topology.yaml)

Purpose: Defines the campus's BGP underlay and VXLAN EVPN overlay — how traffic is forwarded and isolated, independent of physical hardware

- Layer 3+ on top of the physical model — IP addressing, BGP, and EVPN-VXLAN overlay, no cabling/ports of its own
- Single AS (65100) for the whole campus — WAN, core, agg, access all iBGP; only the two ISP links are eBGP
- VNI-to-VLAN mapping table is the single source of truth (6 segments: Users, Cameras, Voice, AP-mgmt, IPTV, Critical-fallback) — referenced by endpoint service model
- Access switches are the EVPN VTEPs (Loopback0 mgmt + Loopback1 VTEP-source); core/agg are pure L3 underlay transit with no VTEP config
- WAN routers interface details are excluded — a filter script (wan_peer_binding) constructs their local port/IP by cross-referencing the physical model and peer IPs
- Two normalization filter scripts do the heavy lifting rendering: one merges wan/core/agg's routing block and access's evpn_vtep block into one common shape; another matches an IP to the device that owns it
- Core routers act as L2VPN EVPN route reflectors — a single evpn_route_reflector: true flag per core is all the model states; a filter script (evpn_rr_peers) derives the full peering scheme from that plus the existing failure_domain grouping (RR mesh between cores, route-reflector-client from each access-VTEP to its own FD's two cores)
- Schema: [logical-topology.schema.json](schemas/logical-topology.schema.json)

[Endpoint Service](models/endpoint%20service.yaml)

Purpose: Standardized security and QoS baseline for endpoint switchports — loop protection, 802.1X/MAB, FHS, and edge QoS

- Per-port switchport policy — VLAN, voice VLAN, security, QoS
- A default_profile applies across a whole range (GigabitEthernet1/0/1-48); port_overrides layer exceptions on top per-interface
- The model uses two different field names for the same access-VLAN concept (native_vlan in the default, access_vlan in overrides) — a filter script is used to reconcile them
- Each override carries a switch field: null/absent applies it to every access switch, a hostname scopes it to just one. This is to allow BAU change (via set_endpoint_port.py) target a single switch/port without touching the rest
- Work together with the acccess role model to produce the switch port configuration. Access role model supplies the switch-wide parameters. This model supply the per port policy.
- Security stack enabled on switch port: 802.1X + MAB, DHCP snooping, IP source guard, dynamic ARP inspection, BPDU guard/portfast
- Schema: [endpoint-service.schema.json](schemas/endpoint-service.schema.json)

[Telemery](models/telemetry.yaml)

Purpose: Model-driven telemetry (MDT) subscriptions — what each device streams, to which collector, and how often

- Three catalogs: telemetry_destinations (collector), sensor_groups (sensor paths + sample interval), role_subscriptions (per-role assignment referencing the other two by name)
- A filter (device_telemetry_subscription()) resolves device_role() → role_subscriptions entry → expands the destination and sensor-group names into full data before the template consume it
- This is the read path back from devices, closing the loop the other three models only open (they declare intent and get pushed; this one reports what's actually happening)
- Schema: [telemetry.schema.json](schemas/telemetry.schema.json)

### Device Role Models

A role is the function of the device performed in the design. This design will utilize 3 role models from an existing product catalog. 

[WAN Edge Role](models/wan%20edge%20role.yaml)

- Applying Platform: Catalyst 8000
- Jinja2 template: [Catalyst 8000.j2](templates/catalyst%208000.j2)
- Schema: [wan-edge-role.schema.json](schemas/wan-edge-role.schema.json)

[Core & Agg Role](models/core%20agg%20role.yaml) 

- Applying Platform Platform: Nexus 93240
- Jinja2 template: [Nexus 93240 j2](templates/nexus%2093240.j2)
- Schema: [core-agg-role.schema.json](schemas/core-agg-role.schema.json)

[Access Role](models/access%20role.yaml) 

- Applying Platform: Catalyst 9000
- Jinja2 template: [Catalyst 9000.j2](templates/catalyst%209000.j2)
- Schema: [access-role.schema.json](schemas/access-role.schema.json)

## Design Validation

The design has gone through data modeling, templating, rendering and deployment stages. It is important to ensure the outcome configuration matchs with the data model. A validation is added to pick up issues during templating, rendering or even deployment. This is done using the [validation playbook](ansible_resources/playbooks/00_validate_render.yml). 

The script will produce the [validation report](validation_report.md)
## Design Deployment (a.k.a Low Level Design)

Prerequisite:
- Management Network has been up and running so that devices are reachable by Ansible runners
- Devices are physically racked and patched according to the patching scheme

### Step 1. Populate the schema in the network source of truth platform (Already done)

### Step 2. Ingest value into the schema to generate data models (Already done)

### Step 3. Setup management connectivity to device

* Submit [patching record](Rack_Patching_Record.md) to facility team for physical setup
* Login to the device and manually configure IP address and gateway for management interface) (Assume management network has been setup)

### Step 4. Make sure the templates and playbooks are loaded onto the Ansible runners hosts

### Step 5. Execute the [Site build master playbook](ansible_resources/playbooks/site.yml) which will execute the corresponding playbooks in sequence:

* [Baseline build](ansible_resources/playbooks/01_baseline_build.yml)
* [Physical topology build](ansible_resources/playbooks/02_physical_topology.yml)
* [Logical topology build](ansible_resources/playbooks/03_logical_topology.yml)
* [Telemetry build](ansible_resources/playbooks/04_streaming_telemetry.yml)

```yaml
ansible-playbook playbooks/site.yml                  # validates, then pushes config to real devices
ansible-playbook playbooks/site.yml -e deploy=false   # validates, renders every stage, saves output, touches no device
```

### Step 6. Execute [service deployment playbook](ansible_resources/playbooks/bau_endpoint_provisioning.yml) to provision the interface on the access switch.

```yaml
ansible-playbook playbooks/bau_endpoint_provisioning.yml \
    -e switch_name=abc-hq-f01-acc-01 -e interface_name=GigabitEthernet1/0/5 \
    -e vlan=20 -e voice_vlan=30 -e description="Marketing desk move, INC0012345"
```

## Config Output

Here is the rendered configurations of a devices, other device's configuration can be found under [config](/config)

<details>
  <summary>abc-hq-wan-01</summary>

```
! ============================================================
! abc-hq-wan-01  (platform: catalyst8000, role: wan-edge)
! Rendered: baseline -> physical topology -> logical topology -> telemetry
! ============================================================

! ---------- 1. Platform baseline (catalyst 8000.j2 + wan edge role.yaml) ----------
!
banner login ^C
Authorized Use Only. System activity is logged.
^C
!
ip domain name campus.example.net
ip domain lookup source-interface Loopback0
!
ip ssh version 2
!
line con 0
 exec-timeout 10 0
 login local
!
line vty 0 15
 exec-timeout 15 0
 transport input ssh
 login local
!
aaa local authentication attempts max-fail 3
!
no ip http server
no ip http secure-server
!
ntp server 10.254.1.10
ntp server 10.254.1.11
ntp source Loopback0
!
logging host 10.254.1.30
logging host 10.254.1.31
logging source-interface Loopback0
logging trap informational
!
snmp-server community CAMPUS-MONITORING-RO RO
snmp-server contact netops@campus.example.net
snmp-server location abc-hq
snmp-server host 10.254.1.20 traps
!
tacacs server TACACS-1
 address ipv4 10.254.1.40
 key DEMO-TACACS-KEY-CHANGE-ME
tacacs server TACACS-2
 address ipv4 10.254.1.41
 key DEMO-TACACS-KEY-CHANGE-ME
ip tacacs source-interface Loopback0
aaa group server tacacs+ TACACS-GROUP
 server name TACACS-1
 server name TACACS-2
aaa authentication login default group TACACS-GROUP local
aaa authorization exec default group TACACS-GROUP local
!
no ip source-route
ip icmp rate-limit unreachable 100
!
! NOTE: the remaining infrastructure_protection settings (accept_redirects,
! proxy_arp, mask_requests) and ipv6_hardening.ra_suppress are applied
! per-interface (no ip redirects / no ip proxy-arp / no ip mask-reply /
! ipv6 nd ra suppress all) -- deferred to the interface-stage template,
! since there are no interfaces to attach them to yet.
!
ip access-list extended fw-in-wan-interface-acl
 remark TODO: define real permit/deny entries for the WAN-facing ACL -- not present in the data model
 remark Placeholder only -- do not deploy as-is
 deny   ip any any log
!
! NOTE: this ACL is defined here as a baseline object but not yet applied to
! an interface (ip access-group fw-in-wan-interface-acl in) -- that
! application, and wan_interfaces.passive_routing_interface, happen at the
! interface stage.
!
ip access-list extended COPP-ACL-ROUTING_UPDATES
 remark BGP control-plane sessions -- the only routing protocol anywhere in
 remark this design's data model (logical_topology.yaml has no OSPF/EIGRP
 remark session defined); extend this ACL if another IGP is ever added.
 permit tcp any eq bgp any
 permit tcp any any eq bgp
!
ip access-list extended COPP-ACL-MANAGEMENT_ACCESS
 remark Device management-plane access -- only matches protocols THIS
 remark device's own management_plane settings actually enable (SSH is
 remark unconditional; SNMP/NTP/TACACS+ only when enabled/non-empty),
 remark same "don't render disabled things" rule the rest of this
 remark template already follows.
 permit tcp any any eq 22
 permit udp any any eq snmp
 permit udp any any eq snmptrap
 permit udp any any eq ntp
 permit tcp any any eq tacacs
!
ip access-list extended COPP-ACL-TRANSIT_TRAFFIC
 remark ICMP hardware-forwarding-exception traffic (unreachables/TTL-exceeded
 remark generation -- icmp_standards.unreachable_rate_limit is always set in
 remark this baseline). ARP is matched separately below via "match protocol
 remark arp" since ARP isn't an IP protocol an ACL can match. This is a
 remark standard CoPP classification pairing, not a value logical_topology.
 remark yaml / platform_wan_baseline.yaml specifies.
 permit icmp any any
!
class-map match-any COPP-ROUTING_UPDATES
 match access-group name COPP-ACL-ROUTING_UPDATES
!
class-map match-any COPP-MANAGEMENT_ACCESS
 match access-group name COPP-ACL-MANAGEMENT_ACCESS
!
class-map match-any COPP-TRANSIT_TRAFFIC
 match access-group name COPP-ACL-TRANSIT_TRAFFIC
 match protocol arp
!
policy-map CONTROL-PLANE-POLICY
 class COPP-ROUTING_UPDATES
  police 32000 conform-action transmit exceed-action drop
  ! priority tier from platform_wan_baseline: "medium" -- rate above is a starting-point placeholder, tune per site
 class COPP-MANAGEMENT_ACCESS
  police 8000 conform-action transmit exceed-action drop
  ! priority tier from platform_wan_baseline: "low" -- rate above is a starting-point placeholder, tune per site
 class COPP-TRANSIT_TRAFFIC
  police 128000 conform-action transmit exceed-action drop
  ! priority tier from platform_wan_baseline: "high" -- rate above is a starting-point placeholder, tune per site
!
control-plane
 service-policy input CONTROL-PLANE-POLICY
!
! NOTE: bgp_security (md5_authentication: True,
! ttl_security_hops: 2) is a per-neighbor
! setting applied under "router bgp <asn>" once the ASN and neighbor list are
! known from logical_topology.yaml -- deferred to that stage. Still flagged
! from the earlier review: confirm ttl_security_hops (physical_topology.yaml
! shows a single-hop ISP circuit, which would argue for 1, not 2) and confirm
! whether wan_interfaces.passive_routing_interface is meant to apply anywhere,
! since BGP has no native passive-interface concept.
!
! NOTE: secure_boot_verification -- Secure Boot on Catalyst 8000 is a
! hardware-anchored (SUDI-based) feature verified automatically at boot;
! there is no standard IOS-XE enable/disable command for it, so no CLI is
! emitted here. Confirm via 'show platform sudi certificate' post-deploy.
! NOTE: hardware_crypto_acceleration -- hardware crypto engine use on
! Catalyst 8000 is governed by the installed throughput/security license
! and platform hardware, not a single confirmed IOS-XE CLI toggle. Verify
! via 'show platform hardware qfp active feature crypto' post-deploy
! rather than assuming a command exists here.
!
end
! ---------- 2. Physical topology (physical topology.j2) ----------
!
hostname abc-hq-wan-01
!
interface TenGigabitEthernet0/0/0
 description EXTERNAL - Service Provider A 10Gbps Ethernet Line (wan_circuit)
 no shutdown
!
interface HundredGigE0/1/0
 description FABRIC - to abc-hq-wan-02 HundredGigE0/1/0 (inter_device)
 no shutdown
!
interface HundredGigE0/2/0
 description FABRIC - to abc-hq-cor-01 HundredGigE0/0/1 (inter_device)
 no shutdown
!
interface HundredGigE0/2/1
 description FABRIC - to abc-hq-cor-03 HundredGigE0/0/1 (inter_device)
 no shutdown
!
! NOTE: abc-hq-wan-01's internal_links in physical_topology.yaml include
! a link to its WAN-tier peer (the horizontal wan-01<->wan-02 interconnect)
! that has no corresponding entry anywhere in logical_topology.yaml's
! bgp_peers for this device -- that physical link is brought up above but
! carries no routing session. Confirm whether it's meant to (e.g. a direct
! iBGP/heartbeat path between the two WAN edges) or is deliberately
! data-plane-only / unused at this stage.
!
end
! ---------- 3. Logical topology (logical topology.j2) ----------
!
interface Loopback0
 ip address 10.0.0.1 255.255.255.255
 description LOOPBACK - management
 no shutdown
!
! NOTE: TenGigabitEthernet0/0/0 carries "eBGP to ISP-A" (peer 192.168.10.1)
! but no local IP can be derived for it -- eBGP peers have no counterpart
! `interfaces:` entry on either side of logical_topology.yaml to derive an
! address from (see FINDING 1). Address must be supplied before deploying.
interface HundredGigE0/2/0
 ip address 10.18.1.0 255.255.255.254
 description UNDERLAY - iBGP to core-01 (FD-A)
!
interface HundredGigE0/2/1
 ip address 10.18.1.2 255.255.255.254
 description UNDERLAY - iBGP Cross-FD to core-03
!
router bgp 65100
 bgp router-id 10.0.0.1
 bgp log-neighbor-changes
 neighbor 192.168.10.1 remote-as 65530
 neighbor 192.168.10.1 description eBGP to ISP-A
 neighbor 192.168.10.1 ttl-security hops 2
 neighbor 192.168.10.1 password !! VAULT-REFERENCE-REQUIRED !!
 neighbor 10.18.1.1 remote-as 65100
 neighbor 10.18.1.1 description iBGP to core-01 (FD-A)
 neighbor 10.18.1.1 ttl-security hops 2
 neighbor 10.18.1.1 password !! VAULT-REFERENCE-REQUIRED !!
 neighbor 10.18.1.3 remote-as 65100
 neighbor 10.18.1.3 description iBGP Cross-FD to core-03
 neighbor 10.18.1.3 ttl-security hops 2
 neighbor 10.18.1.3 password !! VAULT-REFERENCE-REQUIRED !!
 address-family ipv4 unicast
  neighbor 192.168.10.1 activate
  neighbor 10.18.1.1 activate
  neighbor 10.18.1.3 activate
 exit-address-family
!
end
! ---------- 4. Streaming telemetry (telemetry.j2) ----------
!
telemetry ietf subscription 101
 encoding gpb_kv
 filter xpath Cisco-NX-OS-device:System/intf-items
 stream yang-push
 update-policy periodic 3000
 receiver ip address 10.254.1.50 port 57500 protocol grpc-tcp
!
telemetry ietf subscription 102
 encoding gpb_kv
 filter xpath Cisco-NX-OS-device:System/proc-items
 filter xpath Cisco-NX-OS-device:System/eqptmgr-items
 stream yang-push
 update-policy periodic 6000
 receiver ip address 10.254.1.50 port 57500 protocol grpc-tcp
!
! NOTE: update-policy periodic is in centiseconds (1/100s) on IOS-XE MDT,
! not milliseconds -- the value above is telemetry.yaml's
! sample_interval_ms divided by 10. filter xpath values are placeholders
! (see the FINDING above) -- this device's role needs the equivalent
! Cisco-IOS-XE-*-oper YANG xpath before this subscription will actually
! stream anything meaningful; not silently substituted here.
!
end
```
</details>

## Telemetry Output

<!-- <title>Fabric Telemetry</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
  :root{
    --bg:#F3F5F8; --surface:#FFFFFF; --surface-2:#EBEEF3; --border:rgba(15,30,45,0.10);
    --ink:#16202C; --ink-muted:#5C6B82; --ink-faint:#8A96A8;
    --accent:#2E6FA8; --accent-soft:rgba(46,111,168,0.12);
    --good:#1E9E76; --good-soft:rgba(30,158,118,0.14);
    --warn:#B4780E; --warn-soft:rgba(180,120,14,0.14);
    --crit:#C43D34; --crit-soft:rgba(196,61,52,0.13);
    --grid-line:rgba(15,30,45,0.08);
    --shadow: 0 1px 2px rgba(15,30,45,0.06), 0 1px 12px rgba(15,30,45,0.04);
  }
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]){
      --bg:#0B121B; --surface:#121B27; --surface-2:#18222F; --border:rgba(231,236,243,0.09);
      --ink:#E7ECF3; --ink-muted:#8CA0C4; --ink-faint:#647087;
      --accent:#5CA3DE; --accent-soft:rgba(92,163,222,0.16);
      --good:#3FCB9B; --good-soft:rgba(63,203,155,0.14);
      --warn:#E0A526; --warn-soft:rgba(224,165,38,0.14);
      --crit:#E5534B; --crit-soft:rgba(229,83,75,0.15);
      --grid-line:rgba(231,236,243,0.08);
      --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 4px 20px rgba(0,0,0,0.25);
    }
  }
  :root[data-theme="dark"]{
    --bg:#0B121B; --surface:#121B27; --surface-2:#18222F; --border:rgba(231,236,243,0.09);
    --ink:#E7ECF3; --ink-muted:#8CA0C4; --ink-faint:#647087;
    --accent:#5CA3DE; --accent-soft:rgba(92,163,222,0.16);
    --good:#3FCB9B; --good-soft:rgba(63,203,155,0.14);
    --warn:#E0A526; --warn-soft:rgba(224,165,38,0.14);
    --crit:#E5534B; --crit-soft:rgba(229,83,75,0.15);
    --grid-line:rgba(231,236,243,0.08);
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 4px 20px rgba(0,0,0,0.25);
  }

  *{box-sizing:border-box;}
  body{
    background:var(--bg); color:var(--ink);
    font-family:"IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
    padding:28px clamp(16px,3vw,40px) 60px;
  }
  .mono{ font-family:"IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace; }
  .tabular{ font-variant-numeric: tabular-nums; }

  /* ---------- header ---------- */
  header{ display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:16px; margin-bottom:22px; }
  .eyebrow{ font-family:"IBM Plex Mono"; font-size:11px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:var(--accent); margin:0 0 6px; }
  h1{ font-size:26px; font-weight:700; margin:0; letter-spacing:-0.01em; text-wrap:balance; }
  .header-meta{ text-align:right; font-size:12px; color:var(--ink-muted); line-height:1.6; }
  .sim-badge{
    display:inline-flex; align-items:center; gap:6px; font-family:"IBM Plex Mono"; font-size:10.5px; font-weight:600;
    letter-spacing:0.05em; text-transform:uppercase; color:var(--warn); background:var(--warn-soft);
    border:1px solid var(--warn); border-radius:20px; padding:4px 10px; margin-bottom:6px;
  }
  .sim-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:var(--warn); }

  /* ---------- stat tiles ---------- */
  .tiles{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin-bottom:22px; }
  .tile{ background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:16px 18px; box-shadow:var(--shadow); }
  .tile .label{ font-size:11px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:var(--ink-faint); margin-bottom:8px; }
  .tile .value{ font-size:26px; font-weight:700; letter-spacing:-0.01em; }
  .tile .value.good{ color:var(--good); }
  .tile .value.warn{ color:var(--warn); }
  .tile .sub{ font-size:11.5px; color:var(--ink-muted); margin-top:4px; }

  /* ---------- layout ---------- */
  .grid{ display:grid; grid-template-columns:1.35fr 1fr; gap:16px; align-items:start; }
  @media (max-width:920px){ .grid{ grid-template-columns:1fr; } }
  .col{ display:flex; flex-direction:column; gap:16px; }
  .card{ background:var(--surface); border:1px solid var(--border); border-radius:12px; box-shadow:var(--shadow); overflow:hidden; }
  .card-head{ padding:14px 18px 10px; display:flex; align-items:baseline; justify-content:space-between; gap:10px; }
  .card-head h2{ font-size:14.5px; font-weight:700; margin:0; }
  .card-head .meta{ font-size:11px; color:var(--ink-faint); font-family:"IBM Plex Mono"; }
  .card-body{ padding:0 18px 18px; }

  /* ---------- link utilization small multiples ---------- */
  .link-row{ display:grid; grid-template-columns:1fr; gap:10px; }
  .link-item{ padding:10px 0; border-top:1px solid var(--grid-line); }
  .link-item:first-child{ border-top:none; }
  .link-item .lhead{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:4px; gap:8px; }
  .link-item .lname{ font-size:12.5px; font-weight:600; }
  .link-item .lport{ font-family:"IBM Plex Mono"; font-size:10.5px; color:var(--ink-faint); }
  .link-item .lnow{ font-family:"IBM Plex Mono"; font-size:12px; font-weight:600; color:var(--accent); }
  .link-item.incident .lnow{ color:var(--crit); }
  .incident-tag{
    display:inline-flex; align-items:center; gap:4px; font-family:"IBM Plex Mono"; font-size:9.5px; font-weight:600;
    color:var(--crit); background:var(--crit-soft); border-radius:4px; padding:1px 6px; margin-left:6px;
  }

  /* ---------- session table ---------- */
  .table-wrap{ overflow-x:auto; }
  table{ width:100%; border-collapse:collapse; font-size:12.5px; }
  th{ text-align:left; font-size:10.5px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; color:var(--ink-faint); padding:6px 10px; border-bottom:1px solid var(--border); white-space:nowrap; }
  td{ padding:7px 10px; border-bottom:1px solid var(--grid-line); white-space:nowrap; }
  tr.group-row td{ padding-top:14px; font-family:"IBM Plex Mono"; font-size:10.5px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:var(--ink-faint); border-bottom:none; }
  .pair{ font-weight:600; }
  .ip{ font-family:"IBM Plex Mono"; color:var(--ink-muted); }
  .pill{ display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:600; border-radius:20px; padding:2px 9px; }
  .pill::before{ content:""; width:6px; height:6px; border-radius:50%; }
  .pill.good{ color:var(--good); background:var(--good-soft); }
  .pill.good::before{ background:var(--good); }
  .pill.crit{ color:var(--crit); background:var(--crit-soft); }
  .pill.crit::before{ background:var(--crit); }

  /* ---------- device grid ---------- */
  .dev-grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }
  .dev-card{ border:1px solid var(--border); border-radius:8px; padding:10px 12px; background:var(--surface-2); }
  .dev-card .dname{ font-family:"IBM Plex Mono"; font-size:11.5px; font-weight:600; margin-bottom:3px; }
  .role-chip{ font-size:9.5px; color:var(--ink-faint); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:8px; }
  .dev-card .metrics{ display:flex; justify-content:space-between; font-size:11px; color:var(--ink-muted); margin-top:6px; }
  .dev-card .metrics b{ color:var(--ink); font-family:"IBM Plex Mono"; }

  /* ---------- event log ---------- */
  .events{ display:flex; flex-direction:column; }
  .event{ display:grid; grid-template-columns:56px 70px 1fr; gap:10px; padding:8px 0; border-top:1px solid var(--grid-line); font-size:12px; align-items:baseline; }
  .event:first-child{ border-top:none; }
  .event .sev{ font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; padding:2px 0; }
  .event .sev.info{ color:var(--ink-faint); }
  .event .sev.warning{ color:var(--warn); }
  .event .sev.critical{ color:var(--crit); }
  .event .time{ font-family:"IBM Plex Mono"; font-size:11px; color:var(--ink-faint); }
  .event .msg{ color:var(--ink); line-height:1.4; }

  /* ---------- raw sample ---------- */
  .raw-card{ border-left:3px solid var(--crit); }
  pre.raw{
    font-family:"IBM Plex Mono"; font-size:12px; line-height:1.7; margin:0; padding:14px 16px;
    background:var(--surface-2); border-radius:8px; overflow-x:auto; color:var(--ink-muted);
  }
  pre.raw .k{ color:var(--ink); }
  pre.raw .down{ color:var(--crit); font-weight:600; }
  .raw-caption{ font-size:12px; color:var(--ink-muted); margin-top:10px; line-height:1.5; }

  footer{ margin-top:28px; font-size:11px; color:var(--ink-faint); text-align:center; }
</style>

<header>
  <div>
    <p class="eyebrow">abc-hq campus &middot; device deployment domain</p>
    <h1>Fabric Streaming Telemetry</h1>
  </div>
  <div class="header-meta">
    <div class="sim-badge">Simulated feed &mdash; no live collector configured</div><br>
    <span class="mono">collector 10.254.1.50:57500 &middot; encoding gpb-kv</span><br>
    window: last 30 min &middot; 30s sample interval &middot; 12 devices
  </div>
</header>

<div class="tiles" id="tiles"></div>

<div class="grid">
  <div class="col">
    <section class="card">
      <div class="card-head">
        <h2>Fabric Link Utilization</h2>
        <span class="meta">% of link capacity &middot; last 30 min</span>
      </div>
      <div class="card-body">
        <div class="link-row" id="linkRow"></div>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>BGP / EVPN Sessions</h2>
        <span class="meta" id="sessionMeta"></span>
      </div>
      <div class="card-body">
        <div class="table-wrap">
          <table id="sessionTable"></table>
        </div>
      </div>
    </section>
  </div>

  <div class="col">
    <section class="card">
      <div class="card-head">
        <h2>Device CPU &amp; Memory</h2>
        <span class="meta">last 10 min</span>
      </div>
      <div class="card-body">
        <div class="dev-grid" id="devGrid"></div>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Event Log</h2>
        <span class="meta">derived from streamed state, not config</span>
      </div>
      <div class="card-body">
        <div class="events" id="events"></div>
      </div>
    </section>
  </div>
</div>

<section class="card raw-card" style="margin-top:16px;">
  <div class="card-head">
    <h2>Raw Stream Sample</h2>
    <span class="meta">subscription 102 (bgp-evpn) &middot; abc-hq-cor-03 &rarr; abc-hq-f01-acc-02, captured mid-incident</span>
  </div>
  <div class="card-body">
    <pre class="raw" id="rawSample"></pre>
    <p class="raw-caption">This is the decoded GPB-KV payload behind the <b>10:17:30</b> event above &mdash; <span class="mono">state: down</span> on the EVPN address-family is exactly the fact <span class="mono">validate_configs.py</span> cannot see: it confirms a neighbor line was rendered, not that the session is actually up.</p>
  </div>
</section>

<footer>Illustrative dataset &middot; generated to demonstrate what streaming from <span class="mono">telemetry.yaml</span>'s subscriptions would surface once a real collector is listening.</footer>

<script>
const DATA = {"collector": {"ip": "10.254.1.50", "port": 57500, "encoding": "gpb-kv"}, "window_minutes": 30, "sample_interval_s": 30, "link_series": {"abc-hq-wan-01 -> abc-hq-cor-01": {"port": "HundredGigE0/2/0", "utilization": [22, 22.8, 20.0, 18.6, 17.0, 18.4, 19.5, 21.8, 19.3, 18.9, 16.0, 14.4, 14.4, 11.5, 9.7, 10.6, 10.9, 9.2, 9.8, 11.6, 8.7, 10.5, 11.7, 10.7, 8.7, 11.4, 10.4, 8.0, 5.6, 7.6, 8.3, 10.1, 11.5, 11.7, 14.5, 13.8, 14.1, 16.1, 16.8, 19.0, 19.4, 20.7, 17.9, 16.3, 15.1, 12.5, 10.9, 8.5, 7.2, 8.0, 7.2, 6.4, 4.7, 3.3, 5.9, 6.8, 7.4, 5.5, 6.8, 4.8], "errors": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}, "abc-hq-cor-01 -> abc-hq-cor-02": {"port": "HundredGigE0/0/2", "utilization": [38, 37.0, 41.0, 42.1, 42.5, 44.0, 46.7, 49.0, 46.8, 43.0, 41.6, 39.7, 37.4, 40.9, 44.0, 42.5, 43.7, 42.9, 46.2, 45.9, 44.0, 42.0, 42.4, 40.6, 41.2, 44.4, 43.6, 41.4, 45.3, 45.4, 42.1, 38.5, 35.4, 36.4, 38.8, 38.1, 34.6, 33.7, 37.7, 37.9, 41.7, 44.5, 40.6, 42.4, 43.9, 44.2, 42.3, 43.4, 40.3, 39.8, 39.4, 43.0, 46.1, 44.2, 44.2, 41.6, 44.9, 47.9, 46.2, 47.4], "errors": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}, "abc-hq-cor-01 -> abc-hq-agg-01": {"port": "HundredGigE1/0/1", "utilization": [44, 45.1, 41.6, 44.2, 44.6, 47.4, 47.7, 42.7, 41.0, 36.2, 40.5, 44.2, 47.6, 45.6, 41.2, 45.0, 49.5, 45.3, 45.2, 40.9, 43.5, 46.1, 42.4, 42.2, 42.7, 40.3, 44.1, 43.3, 40.4, 40.8, 43.1, 40.1, 38.2, 43.2, 44.7, 44.1, 44.2, 40.4, 37.7, 36.1, 36.9, 34.2, 31.5, 27.2, 28.5, 25.8, 29.8, 33.4, 29.1, 26.5, 28.2, 25.3, 21.7, 26.0, 26.7, 26.4, 29.3, 32.4, 29.3, 25.2], "errors": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}, "abc-hq-agg-01 -> abc-hq-f01-acc-01": {"port": "TenGigabitEthernet1/0/1", "utilization": [31, 30.4, 29.8, 29.6, 31.4, 32.8, 36.7, 33.5, 32.7, 31.4, 34.3, 32.3, 29.8, 29.4, 28.8, 27.0, 25.0, 28.4, 27.9, 30.8, 31.2, 27.6, 31.6, 34.3, 38.0, 41.5, 44.2, 41.6, 41.5, 39.2, 38.4, 34.9, 33.9, 37.8, 35.9, 38.2, 37.8, 37.2, 40.8, 44.8, 45.3, 47.0, 44.2, 42.6, 46.4, 47.0, 47.3, 49.3, 45.8, 46.4, 46.5, 49.3, 46.6, 50.2, 46.9, 44.4, 45.1, 46.5, 44.4, 41.4], "errors": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}, "abc-hq-agg-03 -> abc-hq-f01-acc-02": {"port": "TenGigabitEthernet1/0/1", "utilization": [28, 31.1, 29.1, 29.8, 30.8, 30.2, 30.8, 31.0, 34.5, 32.1, 33.8, 31.8, 30.9, 32.3, 30.7, 29.2, 31.2, 27.8, 27.5, 31.5, 35.4, 32.0, 29.7, 27.9, 31.3, 34.4, 37.4, 36.4, 33.6, 36.3, 37.9, 38.8, 42.7, 43.9, 10.4, 11.1, 6.8, 12.2, 11.9, 33.1, 32.3, 28.8, 37.0, 35.2, 36.1, 37.8, 35.4, 36.5, 34.6, 34.5, 37.8, 40.5, 37.3, 36.7, 34.9, 30.9, 33.1, 34.2, 32.3, 34.2], "errors": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,289,208,406,218,393,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "incident": true}}, "device_data": {"abc-hq-wan-01": {"role": "wan-edge", "platform": "catalyst8000", "cpu": [6, 4.6, 4.2, 5.5, 6.9, 5.6, 5.1, 5.7, 6.2, 5.7, 5.9, 7.0, 8.5, 9.2, 10.5, 9.7, 8.7, 9.6, 8.6, 8.4], "mem": [34, 33.4, 34.2, 34.8, 34.6, 34.9, 35.4, 34.9, 34.2, 34.6, 34.4, 33.5, 33.4, 32.8, 33.6, 33.3, 34.0, 34.7, 34.2, 34.5]}, "abc-hq-wan-02": {"role": "wan-edge", "platform": "catalyst8000", "cpu": [5, 4.7, 4.0, 2.7, 3.6, 3.1, 3.1, 3.7, 4.7, 4.2, 2.8, 3.9, 3.2, 3.4, 4.9, 3.5, 3.8, 3.3, 4.2, 4.0], "mem": [33, 34.0, 33.2, 34.0, 33.4, 32.5, 32.3, 32.4, 33.0, 33.4, 34.2, 34.7, 34.1, 34.0, 34.9, 35.7, 36.0, 36.3, 35.5, 36.3]}, "abc-hq-cor-01": {"role": "core", "platform": "nexus93240", "cpu": [9, 9.0, 9.5, 9.0, 9.6, 9.8, 8.8, 9.3, 9.0, 9.7, 8.7, 8.9, 8.7, 9.7, 9.1, 8.2, 9.1, 9.4, 8.8, 8.7], "mem": [41, 41.4, 41.4, 42.0, 42.9, 43.4, 43.7, 43.2, 43.6, 43.8, 43.0, 43.9, 43.4, 43.0, 43.6, 42.9, 42.0, 43.0, 43.2, 43.7]}, "abc-hq-cor-02": {"role": "core", "platform": "nexus93240", "cpu": [8, 7.9, 9.0, 9.3, 9.9, 9.6, 9.3, 8.2, 8.8, 9.9, 11.0, 12.2, 13.0, 12.2, 13.1, 13.7, 13.6, 13.7, 15.0, 13.9], "mem": [40, 39.3, 39.2, 39.3, 39.4, 39.0, 39.5, 39.4, 40.0, 40.8, 40.7, 41.5, 41.4, 40.7, 41.4, 41.3, 41.8, 42.5, 42.1, 42.6]}, "abc-hq-cor-03": {"role": "core", "platform": "nexus93240", "cpu": [11, 11.0, 10.2, 10.0, 10.6, 9.8, 9.3, 10.5, 9.3, 8.2, 7.9, 6.8, 6.0, 5.7, 5.2, 5.1, 3.8, 4.8, 4.5, 5.3], "mem": [44, 44.9, 43.9, 44.7, 44.8, 44.8, 45.7, 45.3, 45.1, 45.8, 46.5, 46.6, 47.1, 47.7, 48.5, 48.4, 48.0, 47.9, 47.7, 48.1]}, "abc-hq-cor-04": {"role": "core", "platform": "nexus93240", "cpu": [8, 8.9, 9.6, 10.6, 11.8, 13.3, 13.4, 14.6, 14.9, 15.4, 14.1, 13.9, 15.0, 14.1, 13.3, 12.8, 12.7, 12.2, 13.3, 12.7], "mem": [39, 39.9, 39.7, 40.4, 40.4, 40.9, 40.0, 40.9, 40.3, 39.4, 40.4, 39.4, 38.5, 38.0, 38.7, 38.9, 38.4, 38.3, 37.6, 38.5]}, "abc-hq-agg-01": {"role": "aggregation-transit", "platform": "nexus93240", "cpu": [7, 6.9, 6.2, 5.8, 6.1, 7.5, 8.1, 9.0, 8.0, 7.4, 7.6, 8.9, 9.1, 10.4, 10.0, 11.3, 10.4, 10.7, 11.7, 10.9], "mem": [37, 37.4, 37.0, 37.4, 38.0, 38.6, 38.7, 37.8, 37.8, 38.2, 37.3, 37.6, 36.6, 36.5, 36.5, 36.3, 36.0, 36.8, 36.7, 36.1]}, "abc-hq-agg-02": {"role": "aggregation-transit", "platform": "nexus93240", "cpu": [7, 6.0, 6.1, 6.5, 6.9, 8.2, 9.0, 8.9, 9.8, 10.1, 9.6, 8.8, 10.1, 9.5, 9.3, 10.1, 10.3, 10.8, 10.3, 10.3], "mem": [36, 35.7, 35.6, 35.3, 34.9, 34.4, 34.6, 35.4, 35.5, 35.5, 34.9, 34.4, 34.2, 34.3, 33.8, 33.7, 34.2, 34.0, 33.1, 32.7]}, "abc-hq-agg-03": {"role": "aggregation-transit", "platform": "nexus93240", "cpu": [10, 9.7, 8.9, 9.4, 9.0, 9.2, 8.7, 10.2, 10.4, 9.9, 9.8, 9.2, 8.4, 9.1, 8.5, 9.2, 10.6, 11.2, 10.2, 11.0], "mem": [42, 41.6, 41.7, 42.3, 42.4, 43.4, 44.1, 43.7, 43.4, 43.0, 43.4, 42.7, 41.8, 40.9, 40.4, 41.3, 41.6, 42.1, 41.3, 40.3]}, "abc-hq-agg-04": {"role": "aggregation-transit", "platform": "nexus93240", "cpu": [7, 6.4, 6.3, 5.8, 7.2, 6.5, 7.6, 6.4, 5.1, 5.1, 5.3, 5.9, 4.8, 5.7, 7.1, 5.8, 5.1, 5.3, 5.0, 5.3], "mem": [38, 38.2, 38.8, 38.5, 39.4, 39.0, 39.1, 39.0, 39.1, 38.3, 39.2, 38.4, 38.9, 39.1, 38.7, 37.8, 37.3, 37.4, 36.7, 36.6]}, "abc-hq-f01-acc-01": {"role": "access-vtep", "platform": "catalyst9000", "cpu": [12, 12.6, 12.5, 11.1, 10.4, 9.8, 10.9, 9.6, 8.8, 8.1, 8.9, 9.2, 10.1, 9.2, 8.1, 7.2, 6.2, 5.5, 4.4, 3.1], "mem": [47, 47.6, 47.8, 48.4, 49.3, 49.1, 49.1, 48.7, 48.5, 48.0, 48.1, 48.0, 48.2, 49.0, 49.4, 49.6, 48.7, 48.2, 48.5, 49.2]}, "abc-hq-f01-acc-02": {"role": "access-vtep", "platform": "catalyst9000", "cpu": [13, 13.3, 11.8, 12.6, 13.6, 13.8, 14.6, 13.6, 13.7, 13.5, 12.8, 14.3, 14.1, 15.1, 16.5, 16.4, 16.1, 15.6, 14.4, 13.4], "mem": [49, 48.8, 48.8, 49.1, 48.9, 49.5, 48.5, 47.7, 47.2, 46.4, 47.0, 47.7, 48.4, 47.4, 48.1, 48.0, 47.1, 47.2, 47.4, 47.4]}}, "evpn_sessions": [{"a": "abc-hq-cor-01", "b": "abc-hq-cor-02", "kind": "EVPN RR-mesh", "ip": "10.1.0.2", "state": "established", "routes": 41}, {"a": "abc-hq-cor-01", "b": "abc-hq-cor-03", "kind": "EVPN RR-mesh", "ip": "10.1.0.3", "state": "established", "routes": 41}, {"a": "abc-hq-cor-01", "b": "abc-hq-cor-04", "kind": "EVPN RR-mesh", "ip": "10.1.0.4", "state": "established", "routes": 41}, {"a": "abc-hq-cor-02", "b": "abc-hq-cor-03", "kind": "EVPN RR-mesh", "ip": "10.1.0.3", "state": "established", "routes": 41}, {"a": "abc-hq-cor-02", "b": "abc-hq-cor-04", "kind": "EVPN RR-mesh", "ip": "10.1.0.4", "state": "established", "routes": 41}, {"a": "abc-hq-cor-03", "b": "abc-hq-cor-04", "kind": "EVPN RR-mesh", "ip": "10.1.0.4", "state": "established", "routes": 41}, {"a": "abc-hq-cor-01", "b": "abc-hq-f01-acc-01", "kind": "EVPN RR-client", "ip": "10.3.0.1", "state": "established", "routes": 6}, {"a": "abc-hq-cor-02", "b": "abc-hq-f01-acc-01", "kind": "EVPN RR-client", "ip": "10.3.0.1", "state": "established", "routes": 6}, {"a": "abc-hq-cor-03", "b": "abc-hq-f01-acc-02", "kind": "EVPN RR-client", "ip": "10.3.0.2", "state": "established", "routes": 6, "flapped": true}, {"a": "abc-hq-cor-04", "b": "abc-hq-f01-acc-02", "kind": "EVPN RR-client", "ip": "10.3.0.2", "state": "established", "routes": 6, "flapped": true}], "underlay_sessions": [{"a": "abc-hq-wan-01", "b": "abc-hq-cor-01", "kind": "iBGP underlay", "ip": "10.18.1.1", "state": "established"}, {"a": "abc-hq-wan-01", "b": "abc-hq-cor-03", "kind": "iBGP underlay (cross-FD)", "ip": "10.18.1.3", "state": "established"}, {"a": "abc-hq-cor-01", "b": "abc-hq-agg-01", "kind": "iBGP underlay", "ip": "10.9.1.1", "state": "established"}, {"a": "abc-hq-cor-01", "b": "abc-hq-agg-02", "kind": "iBGP underlay", "ip": "10.9.2.1", "state": "established"}, {"a": "abc-hq-agg-01", "b": "abc-hq-f01-acc-01", "kind": "iBGP underlay", "ip": "10.24.1.1", "state": "established"}, {"a": "abc-hq-agg-03", "b": "abc-hq-f01-acc-02", "kind": "iBGP underlay", "ip": "10.24.2.1", "state": "established"}], "events": [{"t": "10:00:00", "sev": "info", "msg": "All 12 devices confirmed streaming — 3 sensor-groups active per device"}, {"t": "10:17:00", "sev": "warning", "msg": "abc-hq-agg-03 Te1/0/1 (to f01-acc-02): CRC errors +842 in 30s sample"}, {"t": "10:17:30", "sev": "critical", "msg": "abc-hq-cor-03 EVPN peer 10.3.0.2 (f01-acc-02, RR-client) → down"}, {"t": "10:18:00", "sev": "critical", "msg": "abc-hq-cor-04 EVPN peer 10.3.0.2 (f01-acc-02, RR-client) → down"}, {"t": "10:19:00", "sev": "info", "msg": "abc-hq-cor-03 EVPN peer 10.3.0.2 → established, 6 routes re-learned"}, {"t": "10:19:30", "sev": "info", "msg": "abc-hq-cor-04 EVPN peer 10.3.0.2 → established, 6 routes re-learned"}, {"t": "10:19:30", "sev": "info", "msg": "abc-hq-agg-03 Te1/0/1 error rate back to baseline"}], "incident_sample_json": {"node_id_str": "abc-hq-cor-03", "subscription_id_str": "102", "encoding_path": "Cisco-NX-OS-device:System/bgp-items", "msg_timestamp": 1757321070123, "data": [{"keys": {"bgp-items/inst-items/dom-items/Dom-list/peer-items/Peer-list/addr": "10.3.0.2"}, "content": {"state": "down", "description": "EVPN RR-client f01-acc-02", "af-name": "l2vpn-evpn", "last-flap-reason": "hold-timer-expired"}}]}};

const svgNS = "http://www.w3.org/2000/svg";

function sparkPath(values, w, h, pad){
  const n = values.length;
  const max = Math.max(...values, 1);
  const min = 0;
  const x = i => pad + (i/(n-1)) * (w - pad*2);
  const y = v => h - pad - ((v-min)/(max-min)) * (h - pad*2);
  let d = "";
  values.forEach((v,i)=>{ d += (i===0? "M":"L") + x(i).toFixed(1) + "," + y(v).toFixed(1) + " "; });
  return {d, lastX:x(n-1), lastY:y(values[n-1]), x, y, max};
}

function buildLinkChart(name, series){
  const w = 560, h = 54, pad=4;
  const {d, lastX, lastY} = sparkPath(series.utilization, w, h, pad);
  const isIncident = !!series.incident;
  const color = isIncident ? "var(--crit)" : "var(--accent)";
  let extra = "";
  if(isIncident){
    // shade the incident window
    const startIdx = series.errors.findIndex(e=>e>0);
    const endIdx = series.errors.length - 1 - [...series.errors].reverse().findIndex(e=>e>0);
    const {x} = sparkPath(series.utilization, w, h, pad);
    extra = `<rect x="${x(startIdx).toFixed(1)}" y="0" width="${(x(endIdx)-x(startIdx)).toFixed(1)}" height="${h}" fill="var(--crit)" opacity="0.10"/>`;
  }
  return `
  <svg width="100%" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" style="display:block;">
    <line x1="0" y1="${h-pad}" x2="${w}" y2="${h-pad}" stroke="var(--grid-line)" stroke-width="1"/>
    ${extra}
    <path d="${d}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="${lastX.toFixed(1)}" cy="${lastY.toFixed(1)}" r="3" fill="${color}"/>
  </svg>`;
}

function buildSparkline(values, color){
  const w = 120, h = 30, pad = 3;
  const {d, lastX, lastY} = sparkPath(values, w, h, pad);
  return `<svg width="100%" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" style="display:block;">
    <path d="${d}" fill="none" stroke="${color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="${lastX.toFixed(1)}" cy="${lastY.toFixed(1)}" r="2.3" fill="${color}"/>
  </svg>`;
}

function short(name){ return name.replace("abc-hq-",""); }

// ---- stat tiles ----
(function(){
  const totalErrors = Object.values(DATA.link_series).reduce((s,l)=>s + l.errors.reduce((a,b)=>a+b,0), 0);
  const cpuLatest = Object.values(DATA.device_data).map(d=>d.cpu[d.cpu.length-1]);
  const avgCpu = (cpuLatest.reduce((a,b)=>a+b,0)/cpuLatest.length).toFixed(1);
  const evpnUp = DATA.evpn_sessions.filter(s=>s.state==="established").length;
  const underlayUp = DATA.underlay_sessions.filter(s=>s.state==="established").length;

  const tiles = [
    {label:"Devices Reporting", value:"12 / 12", cls:"good", sub:"3 sensor-groups each"},
    {label:"Underlay BGP (sample)", value:underlayUp+" / "+DATA.underlay_sessions.length, cls:"good", sub:"representative subset shown"},
    {label:"EVPN / Overlay Sessions", value:evpnUp+" / "+DATA.evpn_sessions.length, cls:"good", sub:"1 flap, recovered at 10:19"},
    {label:"Interface Errors (30 min)", value:totalErrors.toLocaleString(), cls: totalErrors>0 ? "warn":"good", sub:"agg-03 → f01-acc-02, 10:17–10:18"},
    {label:"Avg Fleet CPU", value:avgCpu+"%", cls:"good", sub:"across 12 devices"},
  ];
  document.getElementById("tiles").innerHTML = tiles.map(t=>`
    <div class="tile">
      <div class="label">${t.label}</div>
      <div class="value ${t.cls} tabular">${t.value}</div>
      <div class="sub">${t.sub}</div>
    </div>`).join("");
})();

// ---- link utilization ----
(function(){
  const rows = Object.entries(DATA.link_series).map(([name, series])=>{
    const parts = name.split(" -> ");
    const now = series.utilization[series.utilization.length-1];
    const isIncident = !!series.incident;
    return `
    <div class="link-item ${isIncident?'incident':''}">
      <div class="lhead">
        <span>
          <span class="lname">${short(parts[0])} &rarr; ${short(parts[1])}</span>
          <span class="lport mono">&nbsp;${series.port}</span>
          ${isIncident?'<span class="incident-tag">CRC burst 10:17</span>':''}
        </span>
        <span class="lnow tabular">${now}%</span>
      </div>
      ${buildLinkChart(name, series)}
    </div>`;
  }).join("");
  document.getElementById("linkRow").innerHTML = rows;
})();

// ---- session table ----
(function(){
  document.getElementById("sessionMeta").textContent = (DATA.evpn_sessions.length + DATA.underlay_sessions.length) + " sessions shown of the fabric's full mesh";
  function row(s, kindOverride){
    const stateGood = s.state === "established";
    return `<tr>
      <td class="pair mono">${short(s.a)} ↔ ${short(s.b)}</td>
      <td>${kindOverride || s.kind}</td>
      <td class="ip">${s.ip}</td>
      <td><span class="pill ${stateGood?'good':'crit'}">${stateGood?'Established':'Down'}</span>${s.flapped?'<span class="incident-tag">flapped 10:17</span>':''}</td>
      <td class="tabular">${s.routes!==undefined ? s.routes : '&mdash;'}</td>
    </tr>`;
  }
  const html = `
    <thead><tr><th>Session</th><th>Type</th><th>Peer IP</th><th>State</th><th>Routes</th></tr></thead>
    <tbody>
      <tr class="group-row"><td colspan="5">EVPN Overlay</td></tr>
      ${DATA.evpn_sessions.map(s=>row(s)).join("")}
      <tr class="group-row"><td colspan="5">Underlay (representative)</td></tr>
      ${DATA.underlay_sessions.map(s=>row(s)).join("")}
    </tbody>`;
  document.getElementById("sessionTable").innerHTML = html;
})();

// ---- device grid ----
(function(){
  const cards = Object.entries(DATA.device_data).map(([name,d])=>{
    const cpu = d.cpu[d.cpu.length-1];
    const mem = d.mem[d.mem.length-1];
    return `<div class="dev-card">
      <div class="dname">${short(name)}</div>
      <div class="role-chip">${d.role}</div>
      ${buildSparkline(d.cpu, "var(--accent)")}
      <div class="metrics">
        <span>CPU <b class="tabular">${cpu}%</b></span>
        <span>Mem <b class="tabular">${mem}%</b></span>
      </div>
    </div>`;
  }).join("");
  document.getElementById("devGrid").innerHTML = cards;
})();

// ---- event log ----
(function(){
  document.getElementById("events").innerHTML = DATA.events.map(e=>`
    <div class="event">
      <div class="sev ${e.sev}">${e.sev}</div>
      <div class="time mono">${e.t}</div>
      <div class="msg">${e.msg}</div>
    </div>`).join("");
})();

// ---- raw sample ----
(function(){
  const j = DATA.incident_sample_json;
  const text = JSON.stringify(j, null, 2)
    .replace(/"down"/, '<span class="down">"down"</span>')
    .replace(/"(node_id_str|subscription_id_str|encoding_path|msg_timestamp|keys|content|state|description|af-name|last-flap-reason|data)":/g, '<span class="k">"$1"</span>:');
  document.getElementById("rawSample").innerHTML = text;
})();
</script>
 -->
<div class="box">
  <p>Hello from another file</p>
</div>
