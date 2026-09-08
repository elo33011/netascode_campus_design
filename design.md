# Automation Native Network Design Explain
| Stage | Traditional / Manual Approach | Modern / Automation-Native Approach |
| :--- | :--- | :--- |
| **1. Requirements & Discovery** | • Manual CLI logins (`show version`, `show interface status`) to audit devices individually.<br>• Inventory, port capacity, and IP addresses tracked in offline Excel spreadsheets.<br>• Manual physical walkthroughs for rack space, power, and cooling checks. | • Automated subnet sweeps and API scripts gather real-time inventory and metrics.<br>• Programmatic integration with a single Source of Truth (SoT) like NetBox or Nautobot.<br>• Real-time telemetry streaming (gNMI/Prometheus) to baseline bandwidth and performance. |
| **2. Logical Design** | • Static topology diagrams hand-drawn in Microsoft Visio.<br>• Manual IP subnet calculations logged into static spreadsheets.<br>• Hand-crafted access control lists (ACLs) and static VLAN trunking rules. | • Network intent defined in structured data models (YAML/JSON).<br>• Modular Jinja2 configuration templates stored in version-controlled Git repositories.<br>• Digital Twins and virtual labs (Containerlab, EVE-NG) used to model and test topologies. |
| **3. Physical Staging & Provisioning** | • Physical "bench-building" in a central lab using serial console cables and PuTTY/SecureCRT.<br>• Firmware transferred via local TFTP servers to each switch sequentially.<br>• Configuration built via text editor (Notepad++) copy-pasted line-by-line into the CLI. | • Zero-Touch Provisioning (ZTP): Unboxed devices pull firmware and base configs automatically over DHCP.<br>• GitOps workflow: Changes are submitted via Git Pull Requests with peer code reviews.<br>• Automated CI pipelines run syntax linting and virtual dry-run validations before deployment. |
| **4. Implementation & Deployment** | • On-site "rack-and-stack" with manual cable labelling and hand-held Fluke line testers.<br>• Serial or SSH console access to manually push commands device-by-device.<br>• Cable tracing and link verification done manually by eye or physical inspection. | • Orchestration tools (Ansible, Terraform, Nornir) push configs across hundreds of nodes via APIs (NETCONF/RESTCONF).<br>• Declarative state enforcement detects and automatically reverts manual CLI drift.<br>• Automated LLDP/CDP topology checks immediately verify physical cabling against intent. |
| **5. Validation & Operations** | • Manual failover testing (pulling cords) and typing diagnostic commands (`show ip route`, `ping`, `traceroute`).<br>• Late-night scheduled maintenance windows for manual CLI firmware updates and rollbacks.<br>• Periodic SNMP polling and reactive troubleshooting after users report outages. | • Continuous automated testing frameworks (PyATS, Batfish, Suzieq) run pre/post-change validation.<br>• Continuous sub-second streaming telemetry pushed to real-time dashboards (Grafana, Datadog).<br>• Event-driven closed-loop automation executes automated self-healing and remediation scripts. |

This is a sample enterprise network design to demonstrate how an automation native network design should look like. Automation native design approach incorporates the following elements required by network automation into the classic design process.

- **Determinsitic Topology**: One repeatable pattern, applied consistently everywhere it occurs
- **Abstraction**: Devices generalized into reusable roles, not configured one by one
- **Machine-Friendly interfaces & structured data**: Intent captured as schema-validated data, not prose or diagrams
- **Unique source of truth**: Each fact lives in exactly one place, never restated elsewhere.
- **Declarative state**: State the desired end result; automation works out the steps
- **Streaming Telemetry**: Live device state flows back continuously, not checked on demand

## Difference between traditional and automation native network design approach

Both approaches pass through the same stages — the difference is *how* each stage is done.

| Stage | Traditional Approach | Automation-Native Approach | What Changed |
|---|---|---|---|
| 1. Business requirement | Gather business requirement | Gather business requirement | Unchanged |
| 2. Technical requirement | Translate technical requirement | Translate technical requirement | Unchanged |
| 3. Brainstorm Design options | Create strawman design options (with conceptual diagrams) | Create strawman design options (with AI-rendered conceptual diagrams) | Same step, diagrams can be AI-generated instead of hand-drawn |
| 4. Finalize options with stakeholder| Finalize options | Finalize options | Unchanged |
| 5. High level design (why) | Create high level design | Create high level design — but now designed for determinism, abstraction, and a single source of truth from the outset | Same stage, different task: HLD must commit to a repeatable, parameterizable topology pattern (every floor built the same way) and generalize devices into reusable roles (WAN Edge / Core & Agg / Access), because everything downstream depends on the HLD already being expressible as a pattern + roles rather than bespoke devices |
| 6. BoM | Create BoM | Create BoM | Unchanged |
| 7. Low level design (how) | Create low level design (document) | Define data model schema (physical topology / logical topology / endpoint service) | Same stage, different task: LLD becomes structured, schema-validated data instead of a prose/spreadsheet document |
| 8. Design values | Create rack and patching matrix + obtain IP, ASN, source of truth NMS parameters | Ingest source-of-truth values into the schema → data model | Same stage, different task: two traditional activities (patching matrix, IP/ASN/NMS lookup) both just become values filling the schema defined in stage 7 |
| 9. Config template | Create text-based config template | Create text-based config template (Jinja2) | Same stage, same task in principle — still built once, by hand — but now a parameterized template rather than a per-device text file |
| 10. Deployable config | Create deployable config (manually, per device) | Render deployable config (data model + template = config) | Same stage, different task: generated automatically from stages 7–9, not hand-built per device |
| 11. Runbook & execute | Create procedure-based runbook + execute (manually, by an engineer) | Execute via playbook (playbook + config = deployed config) | Same stage, different task: the playbook performs the steps instead of describing them for a human to type |
| 12. Validate | — (no dedicated stage; verification is ad hoc, done during/after execution) | Validate (data model vs deployed config) | New stage: closes the loop by comparing intent (the data model) against what's actually live on the device |

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



