# Automation Native Network Design Explain

This is a sample network design to demonstrate how an automation native network design should look like. Automation native is a design approach which incorporates the elements required by network automation into design process. These elements are: Determinsitic Topology, Abstraction, Machine-Friendly interfaces & structured data, Unique source of truth, Declarative state and Streaming Telemetry.

Key takeaways:
- Data model first, every content is generated from data models written in yaml
- In this example, data model has already included the values. In real world, this is further broken down to a JSON schema (data model without value). Use Netbox to marry the schema and value together becoming the data model we see here.
- Generated contents includes diagram, racking and stacking plan, cable patching matrix, device baseline configurations and design specific configurations, automated test plan
- Diagram -> Render from data model to svg format (xml)
- Racking and cable patching matrix -> Render from physical data model to table (md)
- Device baseline configuration -> Render from platform data model, Network source of truth, platform specific Jinj2 template, deploy using Ansible
- Design specific configuration -> Render from physical topology data model, logical data model, deploy using Ansible
- Access Switch endpoint facing interface configuration -> Render from the end-point service data model, deploy using Ansible
- The deployment from the initial stage for SoT to end state of config deployed can be managed as workflow using workflow engine to join tie the task together. There will be 2 workflows: one for the build and another for the endpoint services provisioning/deprovisioning.

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

This design is constructed from a set of data models which provides a structure for the "source of truth" information that the automation tools will need. The models are used to render, validate, deploy and maintainthe configurations over automated workflows.

### Design Driven Models

Design driven models define the physical and logical network topology. Endpoint Service has been taken out as a separate data model since it will be frequently reused in BAU.

Every data model below also has a generated JSON Schema under
[`schemas/`](schemas/) -- draft 2020-12, structurally inferred from the
YAML itself (required vs. optional fields, closed vocabularies like link
types and CoPP priority tiers, IPv4/CIDR string patterns) by
[`scripts/generate_schemas.py`](scripts/generate_schemas.py). Regenerate
with `python3 scripts/generate_schemas.py .` after any model change --
every generated schema was checked to both be a valid 2020-12 schema and
to accept its own source YAML without error before being committed here.

| Data Model | Purpose | JSON Schema |
|---|---|---|
| [Physical Topology - Campus Network](models/physical%20topology.yaml) | Ground-truth inventory of campus network hardware and cabling — devices, ports, and interconnects. | [physical-topology.schema.json](schemas/physical-topology.schema.json) |
| [Physical Topology - Management Network](models/physical%20topology%20management%20network.yaml) | Ground-truth inventory of the OOB management network — terminal servers, management switches, and console cabling. | [physical-topology-management-network.schema.json](schemas/physical-topology-management-network.schema.json) |
| [Logical Topology](models/logical%20topology.yaml) | Defines the campus's BGP underlay and VXLAN EVPN overlay — how traffic is forwarded and isolated, independent of physical hardware. | [logical-topology.schema.json](schemas/logical-topology.schema.json) |
| [Endpoint Service](models/endpoint%20service.yaml) | Standardized security and QoS baseline for endpoint switchports — loop protection, 802.1X/MAB, FHS, and edge QoS | [endpoint-service.schema.json](schemas/endpoint-service.schema.json) |

### Device Role Models

Device role model define a standardized, platform-agnostic set of foundational hardening, security, and operational features that must be implemented on every network device. This model will be used in conjunction with a platform specific jinja2 template to render the configuration output required by the platform acting as that role.

| Data Model | Platform Template| JSON Schema |
|---|---|---|
| [WAN Edge Role](models/wan%20edge%20role.yaml) | [Catalyst 8000](templates/catalyst%208000.j2) | [wan-edge-role.schema.json](schemas/wan-edge-role.schema.json) |
| [Core & Agg Role](models/core%20agg%20role.yaml) | [Nexus 93240](templates/nexus%2093240.j2) | [core-agg-role.schema.json](schemas/core-agg-role.schema.json) |
| [Access Role](models/access%20role.yaml) | [Catalyst 9000](templates/catalyst%2090000.j2) | [access-role.schema.json](schemas/access-role.schema.json) |

## Design Deployment

### Step 1. Baseline Build

Prerequisite:
- Management Network has been up and running so that devices are reachable by Ansible runners
- Devices are physically racked and patched according to the patching scheme

Build workflow:
Apply the baseline template for each device -> Validate device local configuration -> Apply physical topology template -> Run point-to-point connectivity validation between devices -> Apply logical topology template -> Run layer 3 connectivity validation, endpoint vlan validation

## Validation

Two independent layers, checking two different things -- neither one
substitutes for the other:

1. **Render-vs-data-model validation (static, pre-deployment)** --
   [`scripts/validate_configs.py`](scripts/validate_configs.py) checks that
   what actually came out of the templates (`rendered_configs/<hostname>.cfg`)
   agrees with what `physical_topology.yaml` / `logical_topology.yaml` / the
   platform role baseline say it should be: every hostname, physical
   interface + description, loopback/logical IP, BGP process and neighbor
   line, NTP/SNMP line, CoPP ACL/class-map, and EVPN VLAN/VNI/SVI the data
   model calls for. It reuses the exact same lookup functions the templates
   call (`device_phys_links`, `device_routing_record`, `wan_peer_binding`,
   `ios_addr`, ...) rather than re-deriving expected values independently,
   so a failure means the template/filter combination itself has a genuine
   defect, not that this script disagrees with the templates for its own
   reasons. This is a regression test for the *build tooling* -- it runs
   before anything ever touches a device, and it does not require any
   device, credential, or Ansible collection to run. Runnable either
   directly (`python3 scripts/validate_configs.py .`) or, preferably, via
   [`playbooks/00_validate_render.yml`](playbooks/00_validate_render.yml)
   (see [Ansible Playbooks](#ansible-playbooks)), which re-renders every
   device, runs the same script, surfaces every individual check as its
   own Ansible task result (`-e validate_verbose=true` to print all of
   them), writes a full per-check `rendered_configs/validation_report.md`,
   and -- unlike running the script by hand -- fails the play (and so
   `site.yml`, which runs it first) if anything doesn't match, so a
   template/filter regression can't reach stage 01's device push at all.
2. **Live-device validation (post-deployment)** -- embedded directly in the
   Ansible playbooks (see [Ansible Playbooks](#ansible-playbooks)):
   facts-gathering after the baseline push, an LLDP neighbor-count check
   against `physical_topology.yaml` after the physical topology push, and a
   BGP-neighbor / endpoint-VLAN presence check against `logical_topology.yaml`
   after the logical topology push. This is the check that the *device*
   actually came up the way the rendered config said it would.

See [Validation Reports](#validation-reports) for the current
`validate_configs.py` run, and `rendered_configs/validation_report.md`
(generated by `playbooks/00_validate_render.yml`) for the full per-check
detail behind it.

## References

### Data Models (Value ingested)
<details>
<summary>Physical Topology - Campus Network </summary>



</details>

<details>
<summary>Physical Topology - Device Management Network </summary>

```yaml
management_context:
  site_code: "abc-hq"
  site_name: "Company ABC Main Campus OOB"

  # ----------------------------------------------------------------------
  # 1. FAILURE DOMAIN & RACK INFRASTRUCTURE DEFINITIONS (MER-level gear only;
  #    floor-level OOB nodes are declared under management_tier.floors below,
  #    same split used in physical_topology.yaml)
  # ----------------------------------------------------------------------
  failure_domains:
    - domain_id: "FD-MGT-A"
      description: "Out-of-Band Management Plane for Production FD-A"
      rack_group: "Suite-A / Left-IDF (co-located with production FD-A racks)"
      racks:
        - rack_id: "RACK-MGT-A01"
          location: "Main Equipment Room - Row A, Rack 3"
          u_space_total: 42
          mounted_devices:
            - { name: "abc-hq-mgt-wan-01", u_position_start: 40, u_height: 1 }
            - { name: "abc-hq-mgt-cor-01", u_position_start: 38, u_height: 1 }
            - { name: "abc-hq-mgt-ts-main-01", u_position_start: 36, u_height: 1 }
            - { name: "abc-hq-mgt-acc-main-01", u_position_start: 34, u_height: 1 }

    - domain_id: "FD-MGT-B"
      description: "Out-of-Band Management Plane for Production FD-B"
      rack_group: "Suite-B / Right-IDF (co-located with production FD-B racks)"
      racks:
        - rack_id: "RACK-MGT-B01"
          location: "Main Equipment Room - Row B, Rack 3"
          u_space_total: 42
          mounted_devices:
            - { name: "abc-hq-mgt-wan-02", u_position_start: 40, u_height: 1 }
            - { name: "abc-hq-mgt-cor-02", u_position_start: 38, u_height: 1 }
            - { name: "abc-hq-mgt-ts-main-02", u_position_start: 36, u_height: 1 }
            - { name: "abc-hq-mgt-acc-main-02", u_position_start: 34, u_height: 1 }

  # ----------------------------------------------------------------------
  # 2. MANAGEMENT LINK SPEED STANDARDS
  # ----------------------------------------------------------------------
  link_standards:
    mgt_wan_circuit: { speed: "1Gbps", media: "1000BASE-T_Copper", description: "Dedicated management WAN connection (console/SSH access)" }
    mgt_backbone: { speed: "10Gbps", media: "10GBASE-SR_Fiber", description: "Connections between Management Core/Access nodes" }
    mgt_ethernet: { speed: "1Gbps", media: "1000BASE-T_Copper", description: "Production device Management GigE port to MGT Switch (SSH)" }
    mgt_console: { speed: "115200bps", media: "Serial-RJ45", description: "Production device Console port to Terminal Server" }

  # ----------------------------------------------------------------------
  # 3. MANAGEMENT IPAM SCHEMA
  # ----------------------------------------------------------------------
  ipam_schema:
    oob_wan_subnet_fd_a: "192.168.100.0/30"   # Dedicated WAN IP space, plane A
    oob_wan_subnet_fd_b: "192.168.100.4/30"   # Dedicated WAN IP space, plane B
    oob_management_loopbacks: "10.254.0.0/19" # Loopbacks for OOB switches, both planes
    oob_console_servers: "10.254.32.0/24"     # Specific for TS/combo nodes, both planes

  # ----------------------------------------------------------------------
  # 4. MANAGEMENT INVENTORY (MER-level: WAN/Core/Access-to-production tier)
  # ----------------------------------------------------------------------
  management_tier:

    mgt_wan_routers:
      - name: "abc-hq-mgt-wan-01"
        failure_domain: "FD-MGT-A"
        rack_location: "RACK-MGT-A01"
        external_links:
          - { interface: "GigabitEthernet0/0/0", type: "mgt_wan_circuit", description: "Dedicated Management WAN line, Plane A" }
        internal_links:
          - { local_port: "TenGigabitEthernet0/1/0", remote_device: "abc-hq-mgt-cor-01", remote_port: "TenGigabitEthernet1/1", type: "mgt_backbone" }

      - name: "abc-hq-mgt-wan-02"
        failure_domain: "FD-MGT-B"
        rack_location: "RACK-MGT-B01"
        external_links:
          - { interface: "GigabitEthernet0/0/0", type: "mgt_wan_circuit", description: "Dedicated Management WAN line, Plane B" }
        internal_links:
          - { local_port: "TenGigabitEthernet0/1/0", remote_device: "abc-hq-mgt-cor-02", remote_port: "TenGigabitEthernet1/1", type: "mgt_backbone" }

    mgt_core_switches:
      - name: "abc-hq-mgt-cor-01"
        failure_domain: "FD-MGT-A"
        rack_location: "RACK-MGT-A01"
        links:
          - { local_port: "TenGigabitEthernet1/1", remote_device: "abc-hq-mgt-wan-01", remote_port: "TenGigabitEthernet0/1/0", type: "mgt_backbone" }
          - { local_port: "TenGigabitEthernet1/2", remote_device: "abc-hq-mgt-ts-main-01", remote_port: "TenGigabitEthernet1/1", type: "mgt_backbone" }
          - { local_port: "TenGigabitEthernet1/3", remote_device: "abc-hq-mgt-acc-main-01", remote_port: "TenGigabitEthernet1/1", type: "mgt_backbone" }
          - { local_port: "TenGigabitEthernet1/4", remote_device: "abc-hq-mgt-oob-f01-01", remote_port: "TenGigabitEthernet1/1", type: "mgt_backbone" } # Floor 1, FD-A; TenGig1/5-1/12 -> floors 2-10, identical pattern

      - name: "abc-hq-mgt-cor-02"
        failure_domain: "FD-MGT-B"
        rack_location: "RACK-MGT-B01"
        links:
          - { local_port: "TenGigabitEthernet1/1", remote_device: "abc-hq-mgt-wan-02", remote_port: "TenGigabitEthernet0/1/0", type: "mgt_backbone" }
          - { local_port: "TenGigabitEthernet1/2", remote_device: "abc-hq-mgt-ts-main-02", remote_port: "TenGigabitEthernet1/1", type: "mgt_backbone" }
          - { local_port: "TenGigabitEthernet1/3", remote_device: "abc-hq-mgt-acc-main-02", remote_port: "TenGigabitEthernet1/1", type: "mgt_backbone" }
          - { local_port: "TenGigabitEthernet1/4", remote_device: "abc-hq-mgt-oob-f01-02", remote_port: "TenGigabitEthernet1/1", type: "mgt_backbone" } # Floor 1, FD-B; TenGig1/5-1/12 -> floors 2-10, identical pattern

    # --- MER-LEVEL ACCESS NODES: console + SSH for WAN/Core/Agg tiers ---
    mgt_access_nodes:
      - name: "abc-hq-mgt-ts-main-01"
        type: "terminal_server"
        failure_domain: "FD-MGT-A"
        rack_location: "RACK-MGT-A01"
        links:
          - { local_port: "TenGigabitEthernet1/1", remote_device: "abc-hq-mgt-cor-01", remote_port: "TenGigabitEthernet1/2", type: "mgt_backbone" }
        async_console_mappings:
          - { async_port: "Async1", description: "Console to wan-01", target_device: "abc-hq-wan-01" }
          - { async_port: "Async2", description: "Console to cor-01", target_device: "abc-hq-cor-01" }
          - { async_port: "Async3", description: "Console to cor-02", target_device: "abc-hq-cor-02" }
          - { async_port: "Async4", description: "Console to agg-01", target_device: "abc-hq-agg-01" }
          - { async_port: "Async5", description: "Console to agg-02", target_device: "abc-hq-agg-02" }

      - name: "abc-hq-mgt-acc-main-01"
        type: "mgt_switch"
        failure_domain: "FD-MGT-A"
        rack_location: "RACK-MGT-A01"
        links:
          - { local_port: "TenGigabitEthernet1/1", remote_device: "abc-hq-mgt-cor-01", remote_port: "TenGigabitEthernet1/3", type: "mgt_backbone" }
        mgt_ethernet_mappings:
          - { mgt_port: "GigabitEthernet1/1", description: "SSH to wan-01 Management0", target_device: "abc-hq-wan-01" }
          - { mgt_port: "GigabitEthernet1/2", description: "SSH to cor-01 mgmt0", target_device: "abc-hq-cor-01" }
          - { mgt_port: "GigabitEthernet1/3", description: "SSH to cor-02 mgmt0", target_device: "abc-hq-cor-02" }
          - { mgt_port: "GigabitEthernet1/4", description: "SSH to agg-01 mgmt0", target_device: "abc-hq-agg-01" }
          - { mgt_port: "GigabitEthernet1/5", description: "SSH to agg-02 mgmt0", target_device: "abc-hq-agg-02" }

      - name: "abc-hq-mgt-ts-main-02"
        type: "terminal_server"
        failure_domain: "FD-MGT-B"
        rack_location: "RACK-MGT-B01"
        links:
          - { local_port: "TenGigabitEthernet1/1", remote_device: "abc-hq-mgt-cor-02", remote_port: "TenGigabitEthernet1/2", type: "mgt_backbone" }
        async_console_mappings:
          - { async_port: "Async1", description: "Console to wan-02", target_device: "abc-hq-wan-02" }
          - { async_port: "Async2", description: "Console to cor-03", target_device: "abc-hq-cor-03" }
          - { async_port: "Async3", description: "Console to cor-04", target_device: "abc-hq-cor-04" }
          - { async_port: "Async4", description: "Console to agg-03", target_device: "abc-hq-agg-03" }
          - { async_port: "Async5", description: "Console to agg-04", target_device: "abc-hq-agg-04" }

      - name: "abc-hq-mgt-acc-main-02"
        type: "mgt_switch"
        failure_domain: "FD-MGT-B"
        rack_location: "RACK-MGT-B01"
        links:
          - { local_port: "TenGigabitEthernet1/1", remote_device: "abc-hq-mgt-cor-02", remote_port: "TenGigabitEthernet1/3", type: "mgt_backbone" }
        mgt_ethernet_mappings:
          - { mgt_port: "GigabitEthernet1/1", description: "SSH to wan-02 Management0", target_device: "abc-hq-wan-02" }
          - { mgt_port: "GigabitEthernet1/2", description: "SSH to cor-03 mgmt0", target_device: "abc-hq-cor-03" }
          - { mgt_port: "GigabitEthernet1/3", description: "SSH to cor-04 mgmt0", target_device: "abc-hq-cor-04" }
          - { mgt_port: "GigabitEthernet1/4", description: "SSH to agg-03 mgmt0", target_device: "abc-hq-agg-03" }
          - { mgt_port: "GigabitEthernet1/5", description: "SSH to agg-04 mgmt0", target_device: "abc-hq-agg-04" }

    # --- FLOOR-LEVEL OOB NODES: one combo console+switch node per FD per
    #     floor, racked alongside the access switch it manages (mirrors
    #     physical_topology.yaml's floors: pattern). Only floor 1 shown;
    #     floors 2-10 follow the identical pattern with cor uplink ports
    #     TenGig1/5 through TenGig1/12.
    floors:
      - floor_number: 1
        oob_nodes:
          - name: "abc-hq-mgt-oob-f01-01"
            type: "combo_console_switch"
            failure_domain: "FD-MGT-A"
            rack_location: "Floor-01 IDF-A Rack 1" # co-located with abc-hq-f01-acc-01
            uplink:
              - { local_port: "TenGigabitEthernet1/1", remote_device: "abc-hq-mgt-cor-01", remote_port: "TenGigabitEthernet1/4", type: "mgt_backbone" }
            async_console_mappings:
              - { async_port: "Async1", description: "Console to f01-acc-01", target_device: "abc-hq-f01-acc-01" }
            mgt_ethernet_mappings:
              - { mgt_port: "GigabitEthernet1/1", description: "SSH to f01-acc-01 mgmt0", target_device: "abc-hq-f01-acc-01" }

          - name: "abc-hq-mgt-oob-f01-02"
            type: "combo_console_switch"
            failure_domain: "FD-MGT-B"
            rack_location: "Floor-01 IDF-B Rack 1" # co-located with abc-hq-f01-acc-02
            uplink:
              - { local_port: "TenGigabitEthernet1/1", remote_device: "abc-hq-mgt-cor-02", remote_port: "TenGigabitEthernet1/4", type: "mgt_backbone" }
            async_console_mappings:
              - { async_port: "Async1", description: "Console to f01-acc-02", target_device: "abc-hq-f01-acc-02" }
            mgt_ethernet_mappings:
              - { mgt_port: "GigabitEthernet1/1", description: "SSH to f01-acc-02 mgmt0", target_device: "abc-hq-f01-acc-02" }
```
</details>

<details>
<summary>Logical Topology</summary>

```yaml

# ============================================================================
# Site Routing, BGP, & VXLAN EVPN Complete Data Model Contract (Corrected: 2 Agg/FD)
# Update: LAYER 3 ROUTED ACCESS VTEPS ONLY (Campus unified AS 65100)
# ============================================================================

site_context:
  site_code: "abc-hq"
  site_name: "Company ABC Main Campus"

  # ============================================================================
  # 1. GLOBAL IPAM & AS SCHEMAS
  # ============================================================================
  ipam_design:
    point_to_point:
      allocation: "schema-driven" # /31 physical interconnects
    loopback:
      allocation: "schema-driven" # Lo0 (Mgmt) & Lo1 (VTEP Source)

  bgp_as_schemas:
    - as_id: "AS_CAMPUS_PRIMARY"
      value: "65100" # All Campus Tiers (WAN, Core, Agg, Acc)
    - as_id: "AS_PROVIDER_A"
      value: "65530"
    - as_id: "AS_PROVIDER_B"
      value: "65531"

  # ============================================================================
  # 2. SERVICE OVERLAY (VXLAN EVPN VTEP)
  # ============================================================================
  evpn_overlay_design:
    vtep_parameters:
      nve_interface: "NVE1"
      vtep_source_interface: "Loopback1"
    # This is still the one place vni_service_mappings is defined --
    # endpoint_services.yaml references vlan_id values from here rather
    # than redefining them, so there's still a single source of truth.
    vni_service_mappings:
      - vni_id: 10
        vlan_id: 10
        name: "Campus_Users"
        description: "Primary user network segment"
        anycast_gateway_ip: "10.10.10.1/24"
        vrf_name: "VRF-CAMPUS-USERS"
        route_distinguisher: "10.3.0.x:10" # x = last octet of the originating access-VTEP's Loopback0
        route_targets:
          import: ["65100:10"]
          export: ["65100:10"]
        dhcp_server: "10.10.100.1"
      # NOTE: VNIs 20, 30, 40, 50, and 999 below only carry the fields
      # originally supplied (vni_id, vlan_id, name, description).
      # anycast_gateway_ip / vrf_name / route_distinguisher / route_targets /
      # dhcp_server were only ever provided for VNI 10 -- not fabricated
      # here for the other five, they still need to be supplied.
      - vni_id: 20
        vlan_id: 20
        name: "Security_Cameras"
        description: "IoT/OT segment for cameras"
      - vni_id: 30
        vlan_id: 30
        name: "Voice_VoIP"
        description: "IP Telephony and VoIP endpoint segment"
      - vni_id: 40
        vlan_id: 40
        name: "Wireless_AP_Mgmt"
        description: "Access Point CAPWAP management infrastructure segment"
      - vni_id: 50
        vlan_id: 50
        name: "IPTV_Multicast"
        description: "Digital signage and IPTV streaming media segment"
      - vni_id: 999
        vlan_id: 999
        name: "Critical_Services"
        description: "Fallback segment (e.g., NAC Server dead)"

  # ============================================================================
  # 3. COMPLETE DEVICE ROUTING, BGP, & INTERCONNECTS
  # ============================================================================
  device_interconnects:

    # --------------------------------------------------------------------------
    # LAYER 1: WAN ROUTERS
    # --------------------------------------------------------------------------
    wan_routers:
    - name: "abc-hq-wan-01"
      failure_domain: "FD-A"
      routing:
        global: { bgp_asn: 65100, router_id: "10.0.0.1" }
        loopbacks: [{ interface: "Loopback0", ip_address: "10.0.0.1/32", type: "management" }]
        bgp_peers:
          - { description: "eBGP to ISP-A", peer_ip: "192.168.10.1", remote_as: 65530, type: "ebgp" }
          - { description: "iBGP to core-01 (FD-A)", peer_ip: "10.18.1.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Cross-FD to core-03", peer_ip: "10.18.1.3", remote_as: 65100, type: "ibgp" }

    - name: "abc-hq-wan-02"
      failure_domain: "FD-B"
      routing:
        global: { bgp_asn: 65100, router_id: "10.0.0.2" }
        loopbacks: [{ interface: "Loopback0", ip_address: "10.0.0.2/32", type: "management" }]
        bgp_peers:
          - { description: "eBGP to ISP-B", peer_ip: "192.168.20.1", remote_as: 65531, type: "ebgp" }
          - { description: "iBGP to core-04 (FD-B)", peer_ip: "10.18.1.4", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Cross-FD to core-02", peer_ip: "10.18.1.2", remote_as: 65100, type: "ibgp" }

    # --------------------------------------------------------------------------
    # LAYER 2: CORE ROUTERS
    # --------------------------------------------------------------------------
    core_routers:
    - name: "abc-hq-cor-01"
      failure_domain: "FD-A"
      routing:
        global: { bgp_asn: 65100, router_id: "10.1.0.1" }
        loopbacks: [{ interface: "Loopback0", ip_address: "10.1.0.1/32", type: "management" }]
        interfaces:
          - { interface: "HundredGigE0/0/1", ip_address: "10.18.1.1/31" } # to wan-01
          - { interface: "HundredGigE0/0/2", ip_address: "10.18.2.1/31" } # to cor-02
          - { interface: "HundredGigE1/0/1", ip_address: "10.9.1.0/31" }  # to agg-01
          - { interface: "HundredGigE1/0/2", ip_address: "10.9.2.0/31" }  # to agg-02
        bgp_peers:
          - { description: "iBGP Underlay to wan-01", peer_ip: "10.18.1.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to cor-02", peer_ip: "10.18.2.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-01", peer_ip: "10.9.1.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-02", peer_ip: "10.9.2.1", remote_as: 65100, type: "ibgp" }

    - name: "abc-hq-cor-02"
      failure_domain: "FD-A"
      routing:
        global: { bgp_asn: 65100, router_id: "10.1.0.2" }
        loopbacks: [{ interface: "Loopback0", ip_address: "10.1.0.2/32", type: "management" }]
        interfaces:
          - { interface: "HundredGigE0/0/1", ip_address: "10.18.1.2/31" } # to wan-02 (Cross-FD)
          - { interface: "HundredGigE0/0/2", ip_address: "10.18.2.0/31" } # to cor-01
          - { interface: "HundredGigE1/0/1", ip_address: "10.9.3.0/31" }  # to agg-01
          - { interface: "HundredGigE1/0/2", ip_address: "10.9.4.0/31" }  # to agg-02
        bgp_peers:
          - { description: "iBGP Underlay to wan-02", peer_ip: "10.18.1.3", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to cor-01", peer_ip: "10.18.2.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-01", peer_ip: "10.9.3.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-02", peer_ip: "10.9.4.1", remote_as: 65100, type: "ibgp" }

    - name: "abc-hq-cor-03"
      failure_domain: "FD-B"
      routing:
        global: { bgp_asn: 65100, router_id: "10.1.0.3" }
        loopbacks: [{ interface: "Loopback0", ip_address: "10.1.0.3/32", type: "management" }]
        interfaces:
          - { interface: "HundredGigE0/0/1", ip_address: "10.18.1.3/31" } # to wan-01 (Cross-FD)
          - { interface: "HundredGigE0/0/2", ip_address: "10.18.3.1/31" } # to cor-04
          - { interface: "HundredGigE1/0/1", ip_address: "10.9.5.0/31" }  # to agg-03
          - { interface: "HundredGigE1/0/2", ip_address: "10.9.6.0/31" }  # to agg-04
        bgp_peers:
          - { description: "iBGP Underlay to wan-01", peer_ip: "10.18.1.2", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to cor-04", peer_ip: "10.18.3.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-03", peer_ip: "10.9.5.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-04", peer_ip: "10.9.6.1", remote_as: 65100, type: "ibgp" }

    - name: "abc-hq-cor-04"
      failure_domain: "FD-B"
      routing:
        global: { bgp_asn: 65100, router_id: "10.1.0.4" }
        loopbacks: [{ interface: "Loopback0", ip_address: "10.1.0.4/32", type: "management" }]
        interfaces:
          - { interface: "HundredGigE0/0/1", ip_address: "10.18.1.4/31" } # to wan-02
          - { interface: "HundredGigE0/0/2", ip_address: "10.18.3.0/31" } # to cor-03
          - { interface: "HundredGigE1/0/1", ip_address: "10.9.7.0/31" }  # to agg-03
          - { interface: "HundredGigE1/0/2", ip_address: "10.9.8.0/31" }  # to agg-04
        bgp_peers:
          - { description: "iBGP Underlay to wan-02", peer_ip: "10.18.1.5", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to cor-03", peer_ip: "10.18.3.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-03", peer_ip: "10.9.7.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-04", peer_ip: "10.9.8.1", remote_as: 65100, type: "ibgp" }

    # --------------------------------------------------------------------------
    # LAYER 3: AGGREGATION SWITCHES (PURE L3 UNDERLAY TRANSIT - 2 PER FD)
    # --------------------------------------------------------------------------
    aggregation_switches:
    - name: "abc-hq-agg-01"
      failure_domain: "FD-A"
      role: "aggregation-transit"
      routing:
        global: { bgp_asn: 65100, router_id: "10.2.0.1" }
        loopbacks:
          - { interface: "Loopback0", ip_address: "10.2.0.1/32", type: "management" }
        interfaces:
          - { interface: "HundredGigE0/1", ip_address: "10.9.0.1/31" } # Up to cor-01
          - { interface: "HundredGigE0/2", ip_address: "10.9.2.1/31" } # Up to cor-02
          - { interface: "HundredGigE0/48", ip_address: "10.15.0.0/31" } # Inter-agg to agg-02
          - { interface: "TenGigabitEthernet1/0/1", ip_address: "10.24.1.0/31" } # Down to f01-acc-01
        bgp_peers:
          - { description: "iBGP Underlay Up to cor-01", peer_ip: "10.9.0.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Up to cor-02", peer_ip: "10.9.2.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-02", peer_ip: "10.15.0.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Down to f01-acc-01", peer_ip: "10.24.1.1", remote_as: 65100, type: "ibgp" }

    - name: "abc-hq-agg-02"
      failure_domain: "FD-A"
      role: "aggregation-transit"
      routing:
        global: { bgp_asn: 65100, router_id: "10.2.0.2" }
        loopbacks:
          - { interface: "Loopback0", ip_address: "10.2.0.2/32", type: "management" }
        interfaces:
          - { interface: "HundredGigE0/1", ip_address: "10.9.4.0/31" } # Up to cor-01
          - { interface: "HundredGigE0/2", ip_address: "10.9.6.0/31" } # Up to cor-02
          - { interface: "HundredGigE0/48", ip_address: "10.15.0.1/31" } # Inter-agg to agg-01
          - { interface: "TenGigabitEthernet1/0/1", ip_address: "10.24.1.2/31" } # Down to f01-acc-01 (cross)
        bgp_peers:
          - { description: "iBGP Underlay Up to cor-01", peer_ip: "10.9.4.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Up to cor-02", peer_ip: "10.9.6.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-01", peer_ip: "10.15.0.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Down to f01-acc-01", peer_ip: "10.24.1.3", remote_as: 65100, type: "ibgp" }

    - name: "abc-hq-agg-03"
      failure_domain: "FD-B"
      role: "aggregation-transit"
      routing:
        global: { bgp_asn: 65100, router_id: "10.2.0.3" }
        loopbacks:
          - { interface: "Loopback0", ip_address: "10.2.0.3/32", type: "management" }
        interfaces:
          - { interface: "HundredGigE0/1", ip_address: "10.9.8.0/31" } # Up to cor-03
          - { interface: "HundredGigE0/2", ip_address: "10.9.10.0/31" } # Up to cor-04
          - { interface: "HundredGigE0/48", ip_address: "10.15.2.0/31" } # Inter-agg to agg-04
          - { interface: "TenGigabitEthernet1/0/1", ip_address: "10.24.2.0/31" } # Down to f01-acc-02
        bgp_peers:
          - { description: "iBGP Underlay Up to cor-03", peer_ip: "10.9.8.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Up to cor-04", peer_ip: "10.9.10.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-04", peer_ip: "10.15.2.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Down to f01-acc-02", peer_ip: "10.24.2.1", remote_as: 65100, type: "ibgp" }

    - name: "abc-hq-agg-04"
      failure_domain: "FD-B"
      role: "aggregation-transit"
      routing:
        global: { bgp_asn: 65100, router_id: "10.2.0.4" }
        loopbacks:
          - { interface: "Loopback0", ip_address: "10.2.0.4/32", type: "management" }
        interfaces:
          - { interface: "HundredGigE0/1", ip_address: "10.9.12.0/31" } # Up to cor-03
          - { interface: "HundredGigE0/2", ip_address: "10.9.14.0/31" } # Up to cor-04
          - { interface: "HundredGigE0/48", ip_address: "10.15.2.1/31" } # Inter-agg to agg-03
          - { interface: "TenGigabitEthernet1/0/1", ip_address: "10.24.2.2/31" } # Down to f01-acc-02 (cross)
        bgp_peers:
          - { description: "iBGP Underlay Up to cor-03", peer_ip: "10.9.12.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Up to cor-04", peer_ip: "10.9.14.1", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-03", peer_ip: "10.15.2.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Down to f01-acc-02", peer_ip: "10.24.2.3", remote_as: 65100, type: "ibgp" }

    # --------------------------------------------------------------------------
    # LAYER 4: LAYER 3 ROUTED ACCESS VTEPS (Floors 1-10)
    # --------------------------------------------------------------------------
    floors:
      - floor_number: 1
        access_vteps:
          - name: "abc-hq-f01-acc-01"
            failure_domain: "FD-A"
            role: "access-vtep"
            evpn_vtep:
              global: { bgp_asn: 65100, router_id: "10.3.0.1" }
              loopbacks:
                - { interface: "Loopback0", ip_address: "10.3.0.1/32", type: "management" }
                - { interface: "Loopback1", ip_address: "10.128.1.1/32", type: "vtep-source" }
              interfaces:
                - interface: "HundredGigabitEthernet1/1/1"
                  description: "FD-A L3 Underlay to agg-01"
                  ip_address: "10.24.1.1/31"
                - interface: "HundredGigabitEthernet1/1/2"
                  description: "Cross-Plane L3 Underlay to agg-02"
                  ip_address: "10.24.1.3/31"
              bgp_peers:
                - description: "iBGP Underlay up to agg-01 (FD-A Master)"
                  peer_ip: "10.24.1.0"
                  remote_as: 65100
                  type: "ibgp"
                - description: "iBGP Underlay cross up to agg-02"
                  peer_ip: "10.24.1.2"
                  remote_as: 65100
                  type: "ibgp"

          - name: "abc-hq-f01-acc-02"
            failure_domain: "FD-B"
            role: "access-vtep"
            evpn_vtep:
              global: { bgp_asn: 65100, router_id: "10.3.0.2" }
              loopbacks:
                - { interface: "Loopback0", ip_address: "10.3.0.2/32", type: "management" }
                - { interface: "Loopback1", ip_address: "10.128.1.2/32", type: "vtep-source" }
              interfaces:
                - interface: "HundredGigabitEthernet1/1/1"
                  description: "FD-B L3 Underlay to agg-03"
                  ip_address: "10.24.2.1/31"
                - interface: "HundredGigabitEthernet1/1/2"
                  description: "Cross-Plane L3 Underlay to agg-04"
                  ip_address: "10.24.2.3/31"
              bgp_peers:
                - description: "iBGP Underlay up to agg-03 (FD-B Master)"
                  peer_ip: "10.24.2.0"
                  remote_as: 65100
                  type: "ibgp"
                - description: "iBGP Underlay cross up to agg-04"
                  peer_ip: "10.24.2.2"
                  remote_as: 65100
                  type: "ibgp"
```
</details>

<details>
<summary>Endpoint Service</summary>

```yaml
site_context:
  site_code: "abc-hq"
  site_name: "Company ABC Main Campus"

  # ----------------------------------------------------------------------
  # 1. LAYER 1/2 ENDPOINT INTERFACE BASELINE (switch-wide defaults)
  # ----------------------------------------------------------------------
  interface_provisioning:
    access_switch_baseline:
      authentication:
        mac_authentication_bypass: true
        dot1x_enabled: true
        fallback_vlan: 999
        guest_vlan: 999
      quality_of_service:
        voice_vlan_trust: true
        ingress_policy_map: "VOICE-PRIORITIZATION"
      spanning_tree:
        bpdu_guard: true
        portfast: true
      ip_dhcp_snooping:
        untrusted_ports_default: true
        mac_address_validation: true

  # ----------------------------------------------------------------------
  # 2. FINE-GRAINED ENDPOINT INTERFACE SPECIFICATIONS (applied profile)
  # ----------------------------------------------------------------------
  endpoint_interfaces:
    default_profile:
      interface_range: "GigabitEthernet1/0/1-48"
      mode: "access"
      native_vlan: 10
      voice_vlan: 30
      administrative_state: true

    first_hop_security:
      dhcp_snooping:
        enabled: true
        trust: false
        rate_limit_pps: 15
      ip_source_guard:
        enabled: true
        binding_check: "ip-mac"
      dai_inspect:
        enabled: true
        logging: "log-buffer"

    authentication_profile:
      dot1x_enabled: true
      mac_authentication_bypass: true
      host_mode: "multi-domain"
      auth_order: ["dot1x", "mab"]
      reauthentication_timer_seconds: 10800
      inactivity_timer_seconds: 3600
      fallback_targets:
        guest_vlan: 999
        auth_fail_vlan: 999
        no_response_vlan: 999

    quality_of_service:
      trust_boundary: "dscp"
      voice_vlan_trust: true
      ingress_policy_map: "VOICE-PRIORITIZATION"
      storm_control:
        unicast_level_percent: 10.0
        multicast_level_percent: 5.0
        broadcast_level_percent: 1.0
        action: "shutdown"

    port_overrides:
      - interface: "GigabitEthernet1/0/1"
        description: "Dedicated Security Camera Access"
        access_vlan: 20
        voice_vlan: null
        dot1x_enabled: false
        mab_enabled: true
      - interface: "GigabitEthernet1/0/48"
        description: "WLC/Access Point Trunk Link"
        mode: "trunk"
        native_vlan: 40
        allowed_vlans: "10,20,30,40,50"
        dot1x_enabled: false
        spanning_tree:
          portfast: false
          bpdu_guard: false
```
</details>

<details>
<summary>WAN Edge Role Device</summary>
  
```yaml
platform_wan_baseline:
  management_plane:
    banner_login: "Authorized Use Only. System activity is logged."
    ssh_version: "2"
    console_timeout_minutes: 10
    vty_timeout_minutes: 15
    login_retries: 3
    dns:
      domain_name: "campus.example.net"
      source_interface: "Loopback0"
    http_services:
      enable: false
      secure_only: true
    ntp:
      servers: ["10.254.1.10", "10.254.1.11"]   # DEMO values -- example internal time sources on the OOB mgmt range, not real servers
      source_interface: "Loopback0"
    syslog:
      servers: []
      source_interface: null
      severity_level: null
    snmp:
      enabled: true
      contact: "netops@campus.example.net"       # DEMO value
      location: "abc-hq"                         # DEMO value
      community_strings: ["CAMPUS-MONITORING-RO"] # DEMO value -- placeholder name, not "public"; replace with a real, generated string before deploying
      trap_destinations: ["10.254.1.20"]          # DEMO value -- example NMS host on the OOB mgmt range
    tacacs:
      servers: []
      source_interface: null
      encryption_key: null

  infrastructure_protection:
    icmp_standards:
      unreachable_rate_limit: 100
      accept_redirects: false
      mask_requests: false
    disabled_ip_services:
      - "ip_source_routing"
      - "proxy_arp"
    ipv6_hardening:
      ra_suppress: true

  routing_baseline:
    bgp_security:
      md5_authentication: true
      ttl_security_hops: 2
    control_plane_policing:
      enable: true
      protocols:
        routing_updates: "medium"
        management_access: "low"
        transit_traffic: "high"

  hardware_integrity:
    secure_boot_verification: true
    hardware_crypto_acceleration: true

  interface_baseline:
    wan_interfaces:
      ingress_acl_name: "fw-in-wan-interface-acl"
      passive_routing_interface: true
```
</details>

<details>
<summary>Core & Aggregation Role Device</summary>
  
```yaml
# ============================================================================
# PLATFORM BASELINE DATA MODEL: CORE & AGGREGATION SWITCHES (Vendor-Agnostic)
# ============================================================================
platform_core_agg_baseline:
  management_plane:
    banner_login: "Authorized Use Only. System activity is logged."
    ssh_version: "2"
    console_timeout_minutes: 10
    vty_timeout_minutes: 15
    login_retries: 3
    dns:
      domain_name: "campus.example.net"
      source_interface: "Loopback0"
    http_services:
      enable: false
      secure_only: true
    ntp:
      servers: []
      source_interface: null
    syslog:
      servers: []
      source_interface: null
      severity_level: null
    snmp:
      enabled: false
      contact: null
      location: null
      community_strings: []
      trap_destinations: []
    tacacs:
      servers: []
      source_interface: null
      encryption_key: null
  infrastructure_protection:
    icmp_standards:
      unreachable_rate_limit: 100
      accept_redirects: false
      mask_requests: false
    disabled_ip_services:
      - "ip_source_routing"
      - "proxy_arp"
    ipv6_hardening:
      ra_suppress: true
  high_availability_and_transit:
    bidirectional_forwarding_detection:
      enable: true
      default_interval_ms: 50
      multiplier: 3
    first_hop_redundancy_protocols:
      preempt: true
      advertisement_interval_seconds: 1
    discovery_protocols:
      cdp_enabled: true
      lldp_enabled: true
  routing_baseline:
    bgp_security:
      md5_authentication: true
      ttl_security_hops: 1
    control_plane_policing:
      enable: true
      protocols:
        routing_updates: "medium"
        management_access: "low"
        transit_traffic: "high"
  hardware_integrity:
    secure_boot_verification: true
    environmental_monitoring: true
  interface_baseline:
    fabric_and_transit_links:
      mtu: 9192
      link_aggregation:
        protocol: "lacp"
        mode: "active"
    unused_ports:
      mode: "routed"
      shutdown: true
    qos_baseline:
      trust_state: "dscp"
```
</details>

<details>
<summary>Access Role Device</summary>
  
```yaml
# ============================================================================
# PLATFORM BASELINE DATA MODEL: ACCESS SWITCH (Vendor-Agnostic)
# ============================================================================
platform_access_baseline:
  management_plane:
    banner_login: "Authorized Use Only. System activity is logged."
    ssh_version: "2"
    console_timeout_minutes: 10
    vty_timeout_minutes: 15
    login_retries: 3
    dns:
      domain_name: "campus.example.net"
      source_interface: "Loopback0"
    http_services:
      enable: false
      secure_only: true
    ntp:
      servers: []
      source_interface: null
    syslog:
      servers: []
      source_interface: null
      severity_level: null
    snmp:
      enabled: false
      contact: null
      location: null
      community_strings: []
      trap_destinations: []
    tacacs:
      servers: []
      source_interface: null
      encryption_key: null
  infrastructure_protection:
    icmp_standards:
      unreachable_rate_limit: 100
      accept_redirects: false
      mask_requests: false
    disabled_ip_services:
      - "ip_source_routing"
      - "proxy_arp"
    ipv6_hardening:
      ra_suppress: true
  endpoint_access_security:
    dot1x_authentication:
      enable: true
      host_mode: "multi-domain"
      fallback_mechanism:
        enabled: true
        restricted_vlan: 998
        reinitialize_timer_seconds: 300
    port_security:
      enable: true
      max_mac_addresses_per_port: 2
      violation_action: "protect"
    dhcp_snooping:
      enable: true
      trust_uplinks_to_transit: true
    dynamic_arp_inspection:
      enable: true
    storm_control:
      broadcast_pps: 500
      multicast_pps: 500
      action: "trap_and_log"
  routing_baseline:
    control_plane_policing:
      enable: true
      protocols:
        routing_updates: "medium"
        management_access: "low"
        transit_traffic: "high"
  hardware_integrity:
    secure_boot_verification: true
    environmental_monitoring: true
  interface_baseline:
    unused_edge_ports:
      mode: "access"
      default_vlan: 999
      shutdown: true
    underlay_uplinks:
      link_aggregation:
        protocol: "lacp"
        mode: "active"
```
</details>

### Jinja2 Templates

<details>

<summary>Jinja2 template - Catalyst 8000</summary>

```jinja2
{# ============================================================================
   Cisco Catalyst 8000 (IOS XE) -- WAN Router Role Baseline Configuration
   ============================================================================
   Stage 1: baseline-only. Renders purely from platform_wan_baseline.yaml --
   management plane, infrastructure protection, routing/CoPP baseline,
   hardware integrity, and the WAN ACL skeleton. No device/topology data is
   expected or used here.

   Deliberately NOT rendered yet, since it depends on physical_topology.yaml
   / logical_topology.yaml rather than the role baseline:
     - hostname
     - interface stanzas (Loopback0, external ISP circuit, internal fabric
       links) and the per-interface hardening (no ip redirects/unreachables/
       proxy-arp/mask-reply) and ACL application (ip access-group ... in)
       that attach to them
     - router bgp (neighbors, router-id, ASN, MD5, ttl-security) -- all of
       it keys off device-specific peer/interface data
   Those will come from a second template (or a second pass merging this
   baseline with per-device topology data) once that stage is ready. The two
   items still needing your confirmation before that stage -- ttl_security_
   hops and passive_routing_interface -- live in platform_wan_baseline.yaml
   itself and will matter once the BGP/interface sections are added back.

   Fields with no confident, standard IOS-XE CLI equivalent are still
   rendered as "! NOTE" comments rather than guessed at -- see
   hardware_integrity below.
   ============================================================================ #}
{% set mp = platform_wan_baseline.management_plane %}
{% set ip_prot = platform_wan_baseline.infrastructure_protection %}
{% set rb = platform_wan_baseline.routing_baseline %}
{% set hw = platform_wan_baseline.hardware_integrity %}
{% set wan_if = platform_wan_baseline.interface_baseline.wan_interfaces %}
!
banner login ^C
{{ mp.banner_login }}
^C
!
{# -------------------------- DNS -------------------------- #}
ip domain name {{ mp.dns.domain_name }}
{% if mp.dns.source_interface %}
ip domain lookup source-interface {{ mp.dns.source_interface }}
{% endif %}
!
{# -------------------------- SSH / lines -------------------------- #}
ip ssh version {{ mp.ssh_version }}
!
line con 0
 exec-timeout {{ mp.console_timeout_minutes }} 0
 login local
!
line vty 0 15
 exec-timeout {{ mp.vty_timeout_minutes }} 0
 transport input ssh
 login local
!
{# login_retries -> local-authentication lockout threshold #}
aaa local authentication attempts max-fail {{ mp.login_retries }}
!
{# -------------------------- HTTP services -------------------------- #}
{% if not mp.http_services.enable %}
no ip http server
no ip http secure-server
{% elif mp.http_services.secure_only %}
no ip http server
ip http secure-server
{% else %}
ip http server
{% endif %}
!
{# -------------------------- NTP -------------------------- #}
{% for server in mp.ntp.servers %}
ntp server {{ server }}
{% endfor %}
{% if mp.ntp.source_interface %}
ntp source {{ mp.ntp.source_interface }}
{% endif %}
{% if not mp.ntp.servers %}
! NOTE: no NTP servers defined in platform_wan_baseline.management_plane.ntp.servers -- add before deploying
{% endif %}
!
{# -------------------------- Syslog -------------------------- #}
{% for server in mp.syslog.servers %}
logging host {{ server }}
{% endfor %}
{% if mp.syslog.source_interface %}
logging source-interface {{ mp.syslog.source_interface }}
{% endif %}
{% if mp.syslog.severity_level %}
logging trap {{ mp.syslog.severity_level }}
{% endif %}
{% if not mp.syslog.servers %}
! NOTE: no syslog servers defined -- add before deploying
{% endif %}
!
{# -------------------------- SNMP -------------------------- #}
{% if mp.snmp.enabled %}
{% for community in mp.snmp.community_strings %}
snmp-server community {{ community }} RO
{% endfor %}
{% if mp.snmp.contact %}
snmp-server contact {{ mp.snmp.contact }}
{% endif %}
{% if mp.snmp.location %}
snmp-server location {{ mp.snmp.location }}
{% endif %}
{% for host in mp.snmp.trap_destinations %}
snmp-server host {{ host }} traps
{% endfor %}
{% else %}
! SNMP disabled per platform_wan_baseline.management_plane.snmp.enabled
{% endif %}
!
{# -------------------------- TACACS+ -------------------------- #}
{% if mp.tacacs.servers %}
{% for server in mp.tacacs.servers %}
tacacs server TACACS-{{ loop.index }}
 address ipv4 {{ server }}
 key {{ mp.tacacs.encryption_key | default('!! VAULT-REFERENCE-REQUIRED !!') }}
{% endfor %}
{% if mp.tacacs.source_interface %}
ip tacacs source-interface {{ mp.tacacs.source_interface }}
{% endif %}
aaa group server tacacs+ TACACS-GROUP
{% for server in mp.tacacs.servers %}
 server name TACACS-{{ loop.index }}
{% endfor %}
aaa authentication login default group TACACS-GROUP local
aaa authorization exec default group TACACS-GROUP local
{% else %}
! NOTE: no TACACS+ servers defined -- falling back to local-only authentication (login local, above)
{% endif %}
!
{# -------------------------- Infrastructure protection (device-wide) -------------------------- #}
{% if 'ip_source_routing' in ip_prot.disabled_ip_services %}
no ip source-route
{% endif %}
ip icmp rate-limit unreachable {{ ip_prot.icmp_standards.unreachable_rate_limit }}
!
! NOTE: the remaining infrastructure_protection settings (accept_redirects,
! proxy_arp, mask_requests) and ipv6_hardening.ra_suppress are applied
! per-interface (no ip redirects / no ip proxy-arp / no ip mask-reply /
! ipv6 nd ra suppress all) -- deferred to the interface-stage template,
! since there are no interfaces to attach them to yet.
!
{# -------------------------- WAN ingress ACL skeleton -------------------------- #}
ip access-list extended {{ wan_if.ingress_acl_name }}
 remark TODO: define real permit/deny entries for the WAN-facing ACL -- not present in the data model
 remark Placeholder only -- do not deploy as-is
 deny   ip any any log
!
! NOTE: this ACL is defined here as a baseline object but not yet applied to
! an interface (ip access-group {{ wan_if.ingress_acl_name }} in) -- that
! application, and wan_interfaces.passive_routing_interface, happen at the
! interface stage.
!
{# -------------------------- Control Plane Policing skeleton -------------------------- #}
{% if rb.control_plane_policing.enable %}
{% set copp_rate = {'low': 8000, 'medium': 32000, 'high': 128000} %}
{% for class_name, priority in rb.control_plane_policing.protocols.items() %}
class-map match-any COPP-{{ class_name | upper }}
 remark TODO: add real match statements (ACL/protocol) for {{ class_name }}
!
{% endfor %}
policy-map CONTROL-PLANE-POLICY
{% for class_name, priority in rb.control_plane_policing.protocols.items() %}
 class COPP-{{ class_name | upper }}
  police {{ copp_rate[priority] }} conform-action transmit exceed-action drop
  ! priority tier from platform_wan_baseline: "{{ priority }}" -- rate above is a starting-point placeholder, tune per site
{% endfor %}
!
control-plane
 service-policy input CONTROL-PLANE-POLICY
!
{% endif %}
{# -------------------------- BGP baseline (ASN-independent security policy) -------------------------- #}
! NOTE: bgp_security (md5_authentication: {{ rb.bgp_security.md5_authentication }},
! ttl_security_hops: {{ rb.bgp_security.ttl_security_hops }}) is a per-neighbor
! setting applied under "router bgp <asn>" once the ASN and neighbor list are
! known from logical_topology.yaml -- deferred to that stage. Still flagged
! from the earlier review: confirm ttl_security_hops (physical_topology.yaml
! shows a single-hop ISP circuit, which would argue for 1, not 2) and confirm
! whether wan_interfaces.passive_routing_interface is meant to apply anywhere,
! since BGP has no native passive-interface concept.
!
{# -------------------------- Hardware integrity -------------------------- #}
{% if hw.secure_boot_verification %}
! NOTE: secure_boot_verification -- Secure Boot on Catalyst 8000 is a
! hardware-anchored (SUDI-based) feature verified automatically at boot;
! there is no standard IOS-XE enable/disable command for it, so no CLI is
! emitted here. Confirm via 'show platform sudi certificate' post-deploy.
{% endif %}
{% if hw.hardware_crypto_acceleration %}
! NOTE: hardware_crypto_acceleration -- hardware crypto engine use on
! Catalyst 8000 is governed by the installed throughput/security license
! and platform hardware, not a single confirmed IOS-XE CLI toggle. Verify
! via 'show platform hardware qfp active feature crypto' post-deploy
! rather than assuming a command exists here.
{% endif %}
!
end

```
</details>

<details>
<summary>Jinja2 template - Nexus 93240</summary>

```jinja2
{# ============================================================================
   Cisco Nexus 93240 (NX-OS) -- Core/Aggregation Role Baseline Configuration
   ============================================================================
   Stage 1: baseline-only, same scope as wan_router_cat8000_iosxe.j2. Renders
   purely from platform_core_agg_baseline.yaml. No device/topology data
   (hostname, interfaces, BGP neighbors, port-channel membership) is
   expected or used here -- those come from physical_topology.yaml /
   logical_topology.yaml at a later stage.

   NX-OS vs IOS-XE differences that matter for this template:
     - Most NX-OS functionality is off until enabled with `feature X` --
       these ARE device-wide (not per-interface), so they're rendered now
       even though the interfaces/protocols they support aren't configured
       yet.
     - Several IOS-style global knobs either don't exist on NX-OS or work
       differently (no `ip source-route` toggle, no direct `ip icmp
       rate-limit unreachable` equivalent -- NX-OS handles this class of
       thing through CoPP instead). Rendered as "! NOTE" rather than
       guessed at, same policy as the WAN template.
     - CoPP on NX-OS is normally applied via a system profile
       (`copp profile <strict|moderate|lenient|dense>`) layered with
       optional custom classes, not built from scratch the way IOS-XE's
       class-map/policy-map is. Both are rendered: a profile as the
       practical baseline, plus the three named custom classes from the
       data model for finer control.

   Also unresolved from the original review of this data model, restated
   here since it's about to become code: first_hop_redundancy_protocols
   doesn't have anywhere to attach in this design -- the access-VTEP layer
   already provides a distributed anycast gateway via EVPN, which is what
   FHRP (HSRP/VRRP) exists to replace. No SVI/HSRP group is configured
   anywhere in physical_topology.yaml or logical_topology.yaml for core/agg
   devices (they're pure L3 underlay transit, per "LAYER 3 ROUTED ACCESS
   VTEPS ONLY"), so this renders as a note, not commands.
   ============================================================================ #}
{% set mp = platform_core_agg_baseline.management_plane %}
{% set ip_prot = platform_core_agg_baseline.infrastructure_protection %}
{% set ha = platform_core_agg_baseline.high_availability_and_transit %}
{% set rb = platform_core_agg_baseline.routing_baseline %}
{% set hw = platform_core_agg_baseline.hardware_integrity %}
{% set ib = platform_core_agg_baseline.interface_baseline %}
!
banner motd #
{{ mp.banner_login }}
#
!
{# -------------------------- DNS -------------------------- #}
ip domain-name {{ mp.dns.domain_name }}
{% if mp.dns.source_interface %}
! NOTE: DNS source-interface pinning on NX-OS is release/platform-dependent
! (not a single universally-documented "ip domain-lookup source-interface"
! knob the way IOS-XE has one) -- verify the exact command for your NX-OS
! version before relying on {{ mp.dns.source_interface }} here.
{% endif %}
!
{# -------------------------- SSH / lines -------------------------- #}
feature ssh
! NOTE: NX-OS's SSH server only supports SSHv2 (no SSHv1 fallback exists
! to disable), so there's no separate "ssh version {{ mp.ssh_version }}"
! command to emit -- feature ssh above is the full equivalent.
!
line console
 exec-timeout {{ mp.console_timeout_minutes }}
!
line vty
 exec-timeout {{ mp.vty_timeout_minutes }}
!
{# login_retries -> NX-OS AAA lockout on repeated failures #}
aaa authentication rejected {{ mp.login_retries }} in 180 ban 60
! NOTE: the "180" (window, seconds) and "60" (ban duration, seconds) above
! aren't in the data model -- only login_retries ({{ mp.login_retries }})
! is. Placeholders; tune per site policy.
!
{# -------------------------- HTTP services -------------------------- #}
{% if not mp.http_services.enable %}
no feature http-server
{% elif mp.http_services.secure_only %}
feature http-server
! NOTE: NX-OS's http-server feature serves both HTTP and HTTPS once
! enabled -- there isn't a clean single-command "HTTPS only" equivalent to
! IOS-XE's "ip http secure-server" (secure_only: true in the model).
! Restrict HTTP access via a management ACL/VRF if plain HTTP must stay
! fully off, rather than assuming a toggle exists here.
{% else %}
feature http-server
{% endif %}
!
{# -------------------------- NTP -------------------------- #}
{% for server in mp.ntp.servers %}
ntp server {{ server }}
{% endfor %}
{% if mp.ntp.source_interface %}
ntp source-interface {{ mp.ntp.source_interface }}
{% endif %}
{% if not mp.ntp.servers %}
! NOTE: no NTP servers defined in platform_core_agg_baseline.management_plane.ntp.servers -- add before deploying
{% endif %}
!
{# -------------------------- Syslog -------------------------- #}
{% for server in mp.syslog.servers %}
{% if mp.syslog.severity_level %}
logging server {{ server }} {{ mp.syslog.severity_level }}
{% else %}
logging server {{ server }}
{% endif %}
{% endfor %}
{% if mp.syslog.source_interface %}
logging source-interface {{ mp.syslog.source_interface }}
{% endif %}
{% if not mp.syslog.servers %}
! NOTE: no syslog servers defined -- add before deploying
{% endif %}
!
{# -------------------------- SNMP -------------------------- #}
{% if mp.snmp.enabled %}
{% for community in mp.snmp.community_strings %}
snmp-server community {{ community }} ro
{% endfor %}
{% if mp.snmp.contact %}
snmp-server contact {{ mp.snmp.contact }}
{% endif %}
{% if mp.snmp.location %}
snmp-server location {{ mp.snmp.location }}
{% endif %}
{% for host in mp.snmp.trap_destinations %}
snmp-server host {{ host }} traps
{% endfor %}
{% else %}
! SNMP disabled per platform_core_agg_baseline.management_plane.snmp.enabled
{% endif %}
!
{# -------------------------- TACACS+ -------------------------- #}
{% if mp.tacacs.servers %}
feature tacacs+
{% for server in mp.tacacs.servers %}
tacacs-server host {{ server }} key {{ mp.tacacs.encryption_key | default('!! VAULT-REFERENCE-REQUIRED !!') }}
{% endfor %}
{% if mp.tacacs.source_interface %}
ip tacacs source-interface {{ mp.tacacs.source_interface }}
{% endif %}
aaa group server tacacs+ TACACS-GROUP
{% for server in mp.tacacs.servers %}
 server {{ server }}
{% endfor %}
aaa authentication login default group TACACS-GROUP
{% else %}
! NOTE: no TACACS+ servers defined -- falling back to local-only authentication
{% endif %}
!
{# -------------------------- Infrastructure protection (device-wide) -------------------------- #}
! NOTE: ip_source_routing (disabled_ip_services) has no corresponding global
! toggle on NX-OS -- the "no ip source-route" command IOS-XE uses doesn't
! exist here; NX-OS's forwarding architecture doesn't process source-routed
! packets via a config knob to disable.
! NOTE: icmp_standards.unreachable_rate_limit ({{ ip_prot.icmp_standards.unreachable_rate_limit }}ms)
! has no direct "ip icmp rate-limit unreachable" equivalent on NX-OS either
! -- this class of protection is normally handled through CoPP (see below)
! rather than a standalone global command. Not rendered as a fabricated
! command.
! NOTE: accept_redirects, proxy_arp, and mask_requests are per-interface
! settings (no ip redirects / no ip proxy-arp / no ip mask-reply-equivalent)
! -- deferred to the interface-stage template, same as ipv6_hardening.ra_suppress.
!
{# -------------------------- High availability & transit (device-wide features) -------------------------- #}
{% if ha.bidirectional_forwarding_detection.enable %}
feature bfd
bfd interval {{ ha.bidirectional_forwarding_detection.default_interval_ms }} min_rx {{ ha.bidirectional_forwarding_detection.default_interval_ms }} multiplier {{ ha.bidirectional_forwarding_detection.multiplier }}
! NOTE: the timers above are the global BFD default; they still need to be
! applied per-neighbor under each routing protocol (e.g. "neighbor <ip> bfd"
! under router bgp) once neighbors are known -- deferred to that stage.
{% endif %}
!
! NOTE: first_hop_redundancy_protocols (preempt: {{ ha.first_hop_redundancy_protocols.preempt }},
! advertisement_interval_seconds: {{ ha.first_hop_redundancy_protocols.advertisement_interval_seconds }})
! has no HSRP/VRRP group to attach to anywhere in this design -- see the
! header note. Not rendered as commands.
!
{% if ha.discovery_protocols.lldp_enabled %}
feature lldp
{% else %}
no feature lldp
{% endif %}
! NOTE: CDP on NX-OS is enabled by default without a global "feature cdp"
! command; cdp_enabled ({{ ha.discovery_protocols.cdp_enabled }}) is
! controlled per-interface ("cdp enable" / "no cdp enable") -- deferred to
! the interface-stage template.
!
{# -------------------------- Routing baseline (device-wide enablement) -------------------------- #}
feature bgp
! NOTE: bgp_security (md5_authentication: {{ rb.bgp_security.md5_authentication }},
! ttl_security_hops: {{ rb.bgp_security.ttl_security_hops }}) is applied
! per-neighbor under "router bgp <asn>" once the ASN and neighbor list are
! known from logical_topology.yaml -- deferred to that stage.
!
{# -------------------------- Control Plane Policing -------------------------- #}
{% if rb.control_plane_policing.enable %}
! Baseline system CoPP profile -- NX-OS's idiomatic starting point.
! "strict" chosen as a reasonable default matching this baseline's
! generally hardened posture; revisit per site if it proves too aggressive
! for legitimate control-plane traffic.
copp profile strict
!
! Custom classes for the three named categories in the data model, layered
! on top of the profile for finer-grained handling than the profile alone
! provides.
{% set copp_rate = {'low': 8000, 'medium': 32000, 'high': 128000} %}
{% for class_name, priority in rb.control_plane_policing.protocols.items() %}
class-map type control-plane match-any COPP-{{ class_name | upper }}
 remark TODO: add real match statements (ACL/protocol) for {{ class_name }}
!
{% endfor %}
policy-map type control-plane COPP-CUSTOM-POLICY
{% for class_name, priority in rb.control_plane_policing.protocols.items() %}
 class COPP-{{ class_name | upper }}
  police cir {{ copp_rate[priority] }} bps conform transmit violate drop
  ! priority tier from platform_core_agg_baseline: "{{ priority }}" -- rate above is a starting-point placeholder, tune per site
{% endfor %}
!
control-plane
 service-policy input copp-system-policy
! NOTE: NX-OS applies CoPP via "service-policy input copp-system-policy"
! referencing the active copp profile; merging the custom
! COPP-CUSTOM-POLICY classes above into that active policy is a
! platform/release-specific step (typically done by editing the generated
! copp-system-policy policy-map, not simply substituting a different policy
! name) -- verify the merge procedure for your NX-OS release before deploying.
{% endif %}
!
{# -------------------------- Interface baseline -------------------------- #}
{% if ib.fabric_and_transit_links.link_aggregation.protocol == 'lacp' %}
feature lacp
{% endif %}
! NOTE: fabric_and_transit_links.mtu ({{ ib.fabric_and_transit_links.mtu }}),
! link_aggregation mode ({{ ib.fabric_and_transit_links.link_aggregation.mode }}),
! unused_ports (mode: {{ ib.unused_ports.mode }}, shutdown: {{ ib.unused_ports.shutdown }}),
! and qos_baseline.trust_state ({{ ib.qos_baseline.trust_state }}) are all
! per-interface -- deferred to the interface-stage template. feature lacp
! above is the one device-wide prerequisite from this section.
!
{# -------------------------- Hardware integrity -------------------------- #}
{% if hw.secure_boot_verification %}
! NOTE: secure_boot_verification -- Secure Boot on Nexus 9000 platforms is a
! hardware-anchored feature verified automatically at boot; there is no
! single confirmed NX-OS enable/disable CLI command for it. Verify via your
! platform's system-integrity/secure-boot show commands for the specific
! N9K model and NX-OS release in use, rather than assuming a command name here.
{% endif %}
{% if hw.environmental_monitoring %}
! NOTE: environmental_monitoring -- fan/power/temperature monitoring runs
! by default in hardware on Nexus 9000 (visible via "show environment");
! there's no single "enable" command for the monitoring itself. The
! actionable equivalent of this flag is usually enabling SNMP environmental
! traps (e.g. "snmp-server enable traps entity") so threshold events
! actually notify someone -- not rendered here since it depends on the SNMP
! trap_destinations configured above; add explicitly if wanted.
{% endif %}
!
end
```
</details>

<details>
<summary>Jinja2 template - Catalyst 9000</summary>

```jinja2
{# ============================================================================
   Cisco Catalyst 9300 (IOS XE) -- Access Switch Role Baseline Configuration
   ============================================================================
   Stage 1: baseline-only, same scope as the WAN and core/agg templates.
   Renders purely from platform_access_baseline.yaml. No device/topology
   data (hostname, interfaces, VLANs, access-VTEP BGP config) is used here.

   Findings from checking this data model against the others before
   building this, worth resolving regardless of template stage:

   1. restricted_vlan: 998 does not exist anywhere in the site's VLAN/VNI
      catalog (logical_topology.yaml's evpn_overlay_design.vni_service_
      mappings only defines 10, 20, 30, 40, 50, 999). If a dot1x fallback
      ever assigns a port to VLAN 998, that VLAN has no VNI mapping, no
      anycast gateway, nothing -- it doesn't exist on the fabric. Compare
      against endpoint_services.yaml, which uses VLAN 999 (Critical_
      Services, which IS defined) for the equivalent guest_vlan/auth_fail_
      vlan/no_response_vlan fields. This looks like it should also be 999,
      not a second, undefined restricted VLAN.

   2. storm_control here (broadcast_pps/multicast_pps: 500, action:
      "trap_and_log") uses different units and a different action than
      endpoint_services.yaml's storm_control (percent-of-bandwidth
      thresholds, action: "shutdown") for what appears to be the same
      concept on the same access ports. Two data models now define storm
      control for the access layer differently -- one of them should be
      the single source of truth, same issue as the evpn_overlay_design
      duplication resolved earlier.

   3. Unlike platform_wan_baseline.yaml and platform_core_agg_baseline.yaml,
      this file has no routing_baseline.bgp_security section -- yet
      access-VTEPs DO speak BGP per logical_topology.yaml (evpn_vtep.
      bgp_peers). Worth confirming whether that omission is intentional
      (e.g. access-tier iBGP considered lower-risk) or a gap to fill in.

   Neither #1 nor #2 blocks rendering this baseline-only stage (both are
   per-interface/per-VLAN settings deferred below regardless), but both
   will matter as soon as the interface stage is built, so they're flagged
   here rather than silently carried into rendered config later.
   ============================================================================ #}
{% set mp = platform_access_baseline.management_plane %}
{% set ip_prot = platform_access_baseline.infrastructure_protection %}
{% set eas = platform_access_baseline.endpoint_access_security %}
{% set rb = platform_access_baseline.routing_baseline %}
{% set hw = platform_access_baseline.hardware_integrity %}
{% set ib = platform_access_baseline.interface_baseline %}
!
banner login ^C
{{ mp.banner_login }}
^C
!
{# -------------------------- DNS -------------------------- #}
ip domain-name {{ mp.dns.domain_name }}
{% if mp.dns.source_interface %}
ip domain lookup source-interface {{ mp.dns.source_interface }}
{% endif %}
!
{# -------------------------- SSH / lines -------------------------- #}
ip ssh version {{ mp.ssh_version }}
!
line con 0
 exec-timeout {{ mp.console_timeout_minutes }} 0
 login local
!
line vty 0 15
 exec-timeout {{ mp.vty_timeout_minutes }} 0
 transport input ssh
 login local
!
aaa local authentication attempts max-fail {{ mp.login_retries }}
!
{# -------------------------- HTTP services -------------------------- #}
{% if not mp.http_services.enable %}
no ip http server
no ip http secure-server
{% elif mp.http_services.secure_only %}
no ip http server
ip http secure-server
{% else %}
ip http server
{% endif %}
!
{# -------------------------- NTP -------------------------- #}
{% for server in mp.ntp.servers %}
ntp server {{ server }}
{% endfor %}
{% if mp.ntp.source_interface %}
ntp source {{ mp.ntp.source_interface }}
{% endif %}
{% if not mp.ntp.servers %}
! NOTE: no NTP servers defined in platform_access_baseline.management_plane.ntp.servers -- add before deploying
{% endif %}
!
{# -------------------------- Syslog -------------------------- #}
{% for server in mp.syslog.servers %}
logging host {{ server }}
{% endfor %}
{% if mp.syslog.source_interface %}
logging source-interface {{ mp.syslog.source_interface }}
{% endif %}
{% if mp.syslog.severity_level %}
logging trap {{ mp.syslog.severity_level }}
{% endif %}
{% if not mp.syslog.servers %}
! NOTE: no syslog servers defined -- add before deploying
{% endif %}
!
{# -------------------------- SNMP -------------------------- #}
{% if mp.snmp.enabled %}
{% for community in mp.snmp.community_strings %}
snmp-server community {{ community }} RO
{% endfor %}
{% if mp.snmp.contact %}
snmp-server contact {{ mp.snmp.contact }}
{% endif %}
{% if mp.snmp.location %}
snmp-server location {{ mp.snmp.location }}
{% endif %}
{% for host in mp.snmp.trap_destinations %}
snmp-server host {{ host }} traps
{% endfor %}
{% else %}
! SNMP disabled per platform_access_baseline.management_plane.snmp.enabled
{% endif %}
!
{# -------------------------- TACACS+ -------------------------- #}
{% if mp.tacacs.servers %}
{% for server in mp.tacacs.servers %}
tacacs server TACACS-{{ loop.index }}
 address ipv4 {{ server }}
 key {{ mp.tacacs.encryption_key | default('!! VAULT-REFERENCE-REQUIRED !!') }}
{% endfor %}
{% if mp.tacacs.source_interface %}
ip tacacs source-interface {{ mp.tacacs.source_interface }}
{% endif %}
aaa group server tacacs+ TACACS-GROUP
{% for server in mp.tacacs.servers %}
 server name TACACS-{{ loop.index }}
{% endfor %}
aaa authentication login default group TACACS-GROUP local
aaa authorization exec default group TACACS-GROUP local
{% else %}
! NOTE: no TACACS+ servers defined -- falling back to local-only authentication (login local, above)
{% endif %}
!
{# -------------------------- Infrastructure protection (device-wide) -------------------------- #}
{% if 'ip_source_routing' in ip_prot.disabled_ip_services %}
no ip source-route
{% endif %}
ip icmp rate-limit unreachable {{ ip_prot.icmp_standards.unreachable_rate_limit }}
!
! NOTE: accept_redirects, proxy_arp, mask_requests, and ipv6_hardening.
! ra_suppress are per-interface -- deferred to the interface-stage template.
!
{# -------------------------- Endpoint access security (device-wide enablement) -------------------------- #}
{% if eas.dot1x_authentication.enable %}
dot1x system-auth-control
{% if eas.dot1x_authentication.fallback_mechanism.enabled %}
dot1x critical eapol
! NOTE: fallback restricted_vlan ({{ eas.dot1x_authentication.fallback_mechanism.restricted_vlan }})
! is applied per-interface ("authentication event fail action authorize
! vlan <n>" / "authentication event no-response action authorize vlan <n>")
! once interfaces exist -- but see the header finding: VLAN
! {{ eas.dot1x_authentication.fallback_mechanism.restricted_vlan }} isn't in
! the site's VLAN catalog. Confirm the correct value (999?) before this is
! wired into the interface stage.
{% endif %}
dot1x timeout reauth-period {{ eas.dot1x_authentication.fallback_mechanism.reinitialize_timer_seconds }}
! NOTE: this sets the global default reauth timer; host_mode ("{{ eas.dot1x_authentication.host_mode }}")
! itself is a per-interface setting, deferred.
{% else %}
no dot1x system-auth-control
{% endif %}
!
! NOTE: port_security (max {{ eas.port_security.max_mac_addresses_per_port }} MAC(s)/port,
! violation action "{{ eas.port_security.violation_action }}") has no global
! enable on IOS-XE -- "switchport port-security ..." only exists under
! interface config. Fully deferred to the interface stage.
!
{% if eas.dhcp_snooping.enable %}
ip dhcp snooping
! NOTE: "ip dhcp snooping vlan <list>" also needs the site's VLAN list
! (logical_topology.yaml's vni_service_mappings: 10,20,30,40,50,999) --
! not rendered here since this stage has no topology data. trust_uplinks_
! to_transit ({{ eas.dhcp_snooping.trust_uplinks_to_transit }}) is per-interface
! ("ip dhcp snooping trust"), deferred.
{% endif %}
!
{% if eas.dynamic_arp_inspection.enable %}
! NOTE: "ip arp inspection vlan <list>" needs the same site VLAN list as
! DHCP snooping above -- not rendered here for the same reason.
{% endif %}
!
! NOTE: storm_control (broadcast_pps/multicast_pps: {{ eas.storm_control.broadcast_pps }}/{{ eas.storm_control.multicast_pps }},
! action: "{{ eas.storm_control.action }}") is entirely per-interface on
! IOS-XE ("storm-control broadcast level pps ...") -- deferred. See header
! finding #2: reconcile against endpoint_services.yaml's conflicting
! percent-based storm_control before this reaches the interface stage.
!
{# -------------------------- Control Plane Policing -------------------------- #}
{% if rb.control_plane_policing.enable %}
{% set copp_rate = {'low': 8000, 'medium': 32000, 'high': 128000} %}
{% for class_name, priority in rb.control_plane_policing.protocols.items() %}
class-map match-any COPP-{{ class_name | upper }}
 remark TODO: add real match statements (ACL/protocol) for {{ class_name }}
!
{% endfor %}
policy-map CONTROL-PLANE-POLICY
{% for class_name, priority in rb.control_plane_policing.protocols.items() %}
 class COPP-{{ class_name | upper }}
  police {{ copp_rate[priority] }} conform-action transmit exceed-action drop
  ! priority tier from platform_access_baseline: "{{ priority }}" -- rate above is a starting-point placeholder, tune per site
{% endfor %}
!
control-plane
 service-policy input CONTROL-PLANE-POLICY
!
! NOTE: this baseline has no routing_baseline.bgp_security section (see
! header finding #3), even though access-VTEPs speak BGP per
! logical_topology.yaml -- nothing to render here as a result; confirm
! whether that's intentional before the BGP/interface stage is built.
{% endif %}
!
{# -------------------------- Hardware integrity -------------------------- #}
{% if hw.secure_boot_verification %}
! NOTE: secure_boot_verification -- Secure Boot on Catalyst 9300 is a
! hardware-anchored (SUDI-based) feature verified automatically at boot;
! there is no standard IOS-XE enable/disable command for it, so no CLI is
! emitted here. Confirm via 'show platform sudi certificate' post-deploy.
{% endif %}
{% if hw.environmental_monitoring %}
! NOTE: environmental_monitoring -- fan/power/temperature monitoring runs
! by default in hardware (visible via 'show environment all'); there's no
! single enable command for the monitoring itself. If threshold alerting is
! wanted, that's normally SNMP environmental traps, which depend on the
! snmp trap_destinations configured above -- not rendered here since it's
! a separate decision from "monitoring exists."
{% endif %}
!
{# -------------------------- Interface baseline -------------------------- #}
! NOTE: unused_edge_ports (mode: {{ ib.unused_edge_ports.mode }}, default_vlan:
! {{ ib.unused_edge_ports.default_vlan }}, shutdown: {{ ib.unused_edge_ports.shutdown }})
! and underlay_uplinks.link_aggregation (protocol: {{ ib.underlay_uplinks.link_aggregation.protocol }},
! mode: {{ ib.underlay_uplinks.link_aggregation.mode }}) are both per-interface
! -- deferred to the interface-stage template. Unlike NX-OS, IOS-XE needs no
! global "feature lacp"-style command, so there is nothing device-wide to
! render for link aggregation at this stage.
!
end
```
</details>

<details>
<summary>Jinja2 template - Physical Topology Deployment</summary>

```jinja2

{# ============================================================================
   Physical Topology Deployment Template (platform-agnostic)
   ============================================================================
   Fills the "Jinja2 template - Physical Topology Deployment" placeholder in
   design.md. Stage 2 of the build workflow (design.md -> "Design
   Deployment" -> "Step 1. Baseline Build"): applied to a device AFTER its
   platform baseline template (catalyst 8000.j2 / nexus 93240.j2 /
   catalyst 9000.j2) and BEFORE logical topology.j2. Renders purely from
   physical_topology.yaml (site_physical_topology) -- Layer 1/2 only: which
   ports exist on this device, bring them up, describe them. Deliberately no
   IP addressing and no BGP here; that's logical topology.j2's job, mirroring
   physical.svg vs logical.svg being modelled as separate concerns.

   Render context expected (one device at a time -- like an Ansible
   `template` task looped over inventory_hostname):
     site_physical_topology : full parsed physical_topology.yaml
     device_name             : hostname being rendered
     platform                : 'catalyst8000' | 'nexus93240' | 'catalyst9000'
                               (see filter_plugins/netascode_filters.py
                               device_platform() -- design.md's Device Role
                               Models table gives the mapping; neither yaml
                               model carries a platform field itself)

   Link discovery: physical_topology.yaml records each physical link from
   ONE side only (e.g. core_routers declares the Core<->Agg link; the
   aggregation_switches entry for that same link is not restated). The
   device_phys_links() filter resolves this by unioning a device's own
   declared links with any other device's entry naming this device as
   remote_device, normalised so the result always reads "this device's local
   port -> that neighbor's port".

   FINDING -- not silently resolved, flagged instead: platform_access_
   baseline.yaml and platform_core_agg_baseline.yaml both set an
   interface_baseline.*.link_aggregation = {protocol: lacp, mode: active}
   for underlay/fabric uplinks. But every fabric/underlay link in this
   topology is a discrete routed point-to-point link to a DIFFERENT
   neighbor (an access switch's two uplinks go to agg-01 and agg-02; a
   core's fabric ports each go to a different agg/wan neighbor) -- nowhere
   does this topology have two links to the SAME neighbor that would need
   bundling into one LACP port-channel. Rendering a port-channel here would
   be wrong: ECMP over independent L3 links is this design's actual
   redundancy mechanism (ties directly to "Deterministic Topology" +
   "Routed Access EVPN-VXLAN Fabric" in design.md's Technical Requirements),
   not link aggregation. No port-channel / LACP config is emitted below;
   confirm with the design owner whether that baseline field is meant for a
   scenario not yet modelled here, or should simply be removed for these
   roles.
   ============================================================================ #}
!
hostname {{ device_name }}
!
{% set ext_links = site_physical_topology | device_external_links(device_name) %}
{% set links = site_physical_topology | device_phys_links(device_name) %}
{% for l in ext_links %}
interface {{ l.interface }}
 description EXTERNAL - {{ l.description }} ({{ l.type }})
 no shutdown
!
{% endfor %}
{% for l in links %}
interface {{ l.local_port }}
 description FABRIC - to {{ l.remote_device }} {{ l.remote_port }} ({{ l.link_type }})
{% if platform in ('nexus93240', 'catalyst9000') %}
 no switchport
{% endif %}
{% if platform == 'nexus93240' %}
 mtu 9192
{% endif %}
{% if platform == 'catalyst9000' and l.link_type == 'agg_to_access' %}
! NOTE: physical_topology.yaml names this port "{{ l.local_port }}" (the
! agg_to_access link_standard is 10Gbps), but logical_topology.yaml's
! evpn_vtep.interfaces entry for this same link on {{ device_name }} names
! it "HundredGigabitEthernet..." -- a 100Gbps interface name. The two
! models disagree on both the interface identifier and the implied port
! speed for the identical physical link. Rendered here under the name
! physical_topology.yaml gives, since design.md's Data Models table states
! that model is the "ground-truth inventory... devices, ports,
! interconnects" -- but this needs correcting in logical_topology.yaml (or
! here, if physical_topology.yaml is the one that's stale) before deploying
! for real.
{% endif %}
 no shutdown
!
{% endfor %}
{% if platform == 'catalyst8000' %}
! NOTE: {{ device_name }}'s internal_links in physical_topology.yaml include
! a link to its WAN-tier peer (the horizontal wan-01<->wan-02 interconnect)
! that has no corresponding entry anywhere in logical_topology.yaml's
! bgp_peers for this device -- that physical link is brought up above but
! carries no routing session. Confirm whether it's meant to (e.g. a direct
! iBGP/heartbeat path between the two WAN edges) or is deliberately
! data-plane-only / unused at this stage.
{% endif %}
!
end
```
</details>

<details>
<summary>Jinja2 template - Logical Topology Deployment</summary>

```jinja2

{# ============================================================================
   Logical Topology Deployment Template (platform-agnostic)
   ============================================================================
   Fills the "Jinja2 template - Logical Topology Deployment" placeholder in
   design.md. Stage 3 of the build workflow -- applied AFTER
   physical_topology.j2 (which brought the ports up and named them). Renders
   from logical_topology.yaml (site_context): loopbacks, per-interface IP
   addressing on the ports physical_topology.j2 already created, underlay
   BGP, and (access-vtep devices only) the EVPN-VXLAN overlay.

   Render context expected (one device at a time):
     site_physical_topology : full parsed physical_topology.yaml (only used
                               here to resolve WAN routers' missing
                               interface bindings, see FINDING 1 below)
     site_context            : full parsed logical_topology.yaml
     device_name, platform, role
     platform_baseline       : whichever of platform_wan_baseline /
                               platform_core_agg_baseline /
                               platform_access_baseline matches this device
                               (reused from the baseline-stage template so
                               routing_baseline.bgp_security is available)

   FINDING 1 -- wan_routers in logical_topology.yaml have no `interfaces:`
   list (core_routers, aggregation_switches and access_vteps all do). Their
   bgp_peers only carry peer_ip, not which local interface or local IP the
   session rides on -- this is the exact gap catalyst 8000.j2's own header
   already flagged ("all of it keys off device-specific peer/interface
   data"). wan_peer_binding() resolves it two ways: the eBGP peer is
   assumed to ride the device's one external ISP circuit (true for both WAN
   routers here); each iBGP peer's remote device is found by matching
   peer_ip against every OTHER device's logical-topology interfaces list,
   then the physical link to that device supplies the local port, and the
   device's own /31 address is derived (RFC 3021: the other half of the
   peer's /31). Anywhere this can't be resolved, a NOTE is rendered instead
   of a guessed command.

   FINDING 2 -- physical_topology.yaml and logical_topology.yaml both use
   IOS-style interface names (HundredGigE0/0/1, TenGigabitEthernet1/0/1,
   ...) for EVERY device, including core_routers/aggregation_switches,
   which design.md's Device Role Models table maps to Nexus 93240 (NX-OS).
   Real NX-OS interface names follow a different convention (e.g.
   Ethernet1/1), so the interface names below are almost certainly
   placeholders rather than the real hardware-verified port names for that
   platform. Rendered literally as the data model gives them (renaming
   them would be guessing a real NX-OS slot/port layout that isn't in
   scope of these two yaml files) -- flag for correction before deploying
   against real Nexus 93240 hardware.

   FINDING 3 -- there is no BGP EVPN overlay peering anywhere in this data
   model. Each access-vtep's bgp_peers are underlay-only iBGP sessions to
   its two local aggregation switches (which are themselves declared
   "role: aggregation-transit", pure L3 forwarders with no VTEP/EVPN
   config at all). For EVPN-VXLAN to actually distribute MAC/IP routes
   between abc-hq-f01-acc-01 and abc-hq-f01-acc-02, something has to run
   the L2VPN EVPN address-family between the access-VTEPs (or a
   route-reflector each peers to) -- normally their shared Loopback0/
   Loopback1 space, or an RR seated at the core. That layer isn't defined
   anywhere in logical_topology.yaml. `router bgp` / `address-family
   l2vpn evpn` is still rendered below (NVE and per-VNI config are
   meaningless without it), but with no neighbor activated under it --
   this is flagged as a real design gap, not filled in with an assumed RR.
   ============================================================================ #}
{% set rtg = site_context | device_routing_record(device_name) %}
{% set bgp_sec = platform_baseline.routing_baseline.bgp_security if platform_baseline.routing_baseline is defined and platform_baseline.routing_baseline.bgp_security is defined else none %}
!
{% for lb in rtg.loopbacks %}
interface {{ lb.interface }}
{% if platform == 'nexus93240' %}
 ip address {{ lb.ip_address }}
{% else %}
 ip address {{ lb.ip_address | ios_addr }}
{% endif %}
 description LOOPBACK - {{ lb.type }}
 no shutdown
!
{% endfor %}
{% if not bgp_sec %}
! NOTE: {{ platform }} has no routing_baseline.bgp_security section in its
! platform baseline yaml (platform_access_baseline.yaml has none at all --
! see catalyst 9000.j2's own header finding #3), yet this device speaks
! BGP per logical_topology.yaml. Neighbors below carry no ttl-security /
! password lines as a result -- confirm whether that's intentional.
{% endif %}
{# -------------------------- Per-interface IP addressing -------------------------- #}
{% if rtg.interfaces %}
{% for i in rtg.interfaces %}
interface {{ i.interface }}
{% if platform == 'nexus93240' %}
 ip address {{ i.ip_address }}
{% else %}
 ip address {{ i.ip_address | ios_addr }}
{% endif %}
{% if i.description is defined %}
 description {{ i.description }}
{% endif %}
!
{% endfor %}
{% else %}
{% for p in rtg.bgp_peers %}
{% set b = site_physical_topology | wan_peer_binding(site_context, device_name, p) %}
{% if b.resolved and b.own_ip %}
interface {{ b.local_port }}
 ip address {{ b.own_ip | ios_addr }}
 description UNDERLAY - {{ p.description }}
!
{% elif b.resolved %}
! NOTE: {{ b.local_port }} carries "{{ p.description }}" (peer {{ p.peer_ip }})
! but no local IP can be derived for it -- eBGP peers have no counterpart
! `interfaces:` entry on either side of logical_topology.yaml to derive an
! address from (see FINDING 1). Address must be supplied before deploying.
{% else %}
! NOTE: could not resolve which physical interface carries "{{ p.description }}"
! (peer {{ p.peer_ip }}) for {{ device_name }} -- no other device's
! logical_topology.yaml `interfaces:` entry has this peer_ip. Skipped
! rather than guessed.
{% endif %}
{% endfor %}
{% endif %}
{# -------------------------- Underlay BGP -------------------------- #}
router bgp {{ rtg.global.bgp_asn }}
{% if platform == 'nexus93240' %}
 router-id {{ rtg.global.router_id }}
{% else %}
 bgp router-id {{ rtg.global.router_id }}
 bgp log-neighbor-changes
{% endif %}
{% for p in rtg.bgp_peers %}
 neighbor {{ p.peer_ip }} remote-as {{ p.remote_as }}
{% if platform == 'nexus93240' %}
  description {{ p.description }}
{% if bgp_sec %}
  ttl-security hops {{ bgp_sec.ttl_security_hops }}
{% if bgp_sec.md5_authentication %}
  password !! VAULT-REFERENCE-REQUIRED !!
{% endif %}
{% endif %}
  address-family ipv4 unicast
{% else %}
 neighbor {{ p.peer_ip }} description {{ p.description }}
{% if bgp_sec %}
 neighbor {{ p.peer_ip }} ttl-security hops {{ bgp_sec.ttl_security_hops }}
{% if bgp_sec.md5_authentication %}
 neighbor {{ p.peer_ip }} password !! VAULT-REFERENCE-REQUIRED !!
{% endif %}
{% endif %}
{% endif %}
{% endfor %}
{% if platform != 'nexus93240' %}
 address-family ipv4 unicast
{% for p in rtg.bgp_peers %}
  neighbor {{ p.peer_ip }} activate
{% endfor %}
 exit-address-family
{% endif %}
{# -------------------------- EVPN-VXLAN overlay (access-vtep only) -------------------------- #}
{% if rtg.kind == 'access-vtep' %}
{% set evpn = site_context.evpn_overlay_design %}
{% set lo0 = rtg.loopbacks | selectattr('type', 'equalto', 'management') | map(attribute='ip_address') | first %}
{% set lo1_iface = rtg.loopbacks | selectattr('type', 'equalto', 'vtep-source') | map(attribute='interface') | first %}
!
{% for vni in evpn.vni_service_mappings %}
{% if vni.vrf_name is defined %}
vrf definition {{ vni.vrf_name }}
 rd {{ vni.route_distinguisher | resolve_rd(lo0) }}
 address-family ipv4
{% for rt in vni.route_targets.import %}
  route-target import {{ rt }}
{% endfor %}
{% for rt in vni.route_targets.export %}
  route-target export {{ rt }}
{% endfor %}
 exit-address-family
!
{% endif %}
vlan configuration {{ vni.vlan_id }}
 member vni {{ vni.vni_id }}
!
{% if vni.anycast_gateway_ip is defined %}
interface vlan{{ vni.vlan_id }}
 description {{ vni.name }} - {{ vni.description }}
 vrf forwarding {{ vni.vrf_name }}
 ip address {{ vni.anycast_gateway_ip | ios_addr }}
 no ip redirects
 fabric forwarding mode anycast-gateway
{% if vni.dhcp_server is defined %}
 ip helper-address {{ vni.dhcp_server }}
{% endif %}
 no shutdown
!
{% else %}
! NOTE: VNI {{ vni.vni_id }} ({{ vni.name }}) has no anycast_gateway_ip /
! vrf_name in logical_topology.yaml (only vni_id, vlan_id, name,
! description were ever supplied for it -- see that file's own header
! comment). Rendered as an L2-only VNI extension with no SVI/anycast
! gateway; confirm whether it's meant to stay L2-only (plausible for
! Security_Cameras/Voice/Wireless-Mgmt/IPTV/Critical-Services) or is
! simply incomplete data.
{% endif %}
{% endfor %}
!
interface nve1
 source-interface {{ lo1_iface }}
 host-reachability protocol bgp
{% for vni in evpn.vni_service_mappings %}
{% if vni.vrf_name is defined %}
 member vni {{ vni.vni_id }} vrf {{ vni.vrf_name }}
{% else %}
 member vni {{ vni.vni_id }}
  ingress-replication protocol bgp
{% endif %}
{% endfor %}
 no shutdown
!
router bgp {{ rtg.global.bgp_asn }}
 address-family l2vpn evpn
! NOTE: no neighbor is activated under this address-family -- see header
! FINDING 3. Nothing in logical_topology.yaml defines an EVPN overlay
! peer (route-reflector or full-mesh) between access-VTEPs; the two
! underlay iBGP peers above only carry the IPv4 underlay, not L2VPN EVPN.
! member vni configuration above is inert until this is resolved.
{% endif %}
!
end
```
</details>

<details>
<summary>Jinja2 template - Service Deployment</summary>

```jinja2

```
</details>

### Ansible Playbooks

Implements design.md's own "Step 1. Baseline Build" workflow (apply
baseline -> validate -> apply physical topology -> validate p2p
connectivity -> apply logical topology -> validate L3/vlan) as three
per-stage playbooks plus an orchestrator, all against the same
`templates/*.j2` + `filter_plugins/netascode_filters.py` that
`scripts/render_configs.py` uses -- one set of templates and lookup
filters, driven by either tool, so there's no second copy of "how a
device's config is built" to keep in sync.

| File | Stage |
|---|---|
| [`inventory/hosts.yml`](inventory/hosts.yml) | Devices grouped by `ansible_network_os` (wan_edge/core_agg/access); platform + role are derived at runtime from the hostname via `device_platform`/`device_role`, not duplicated here |
| [`inventory/group_vars/all.yml`](inventory/group_vars/all.yml) | `platform_map` (platform -> role-baseline yaml + template), `repo_root`, `deploy` toggle |
| [`playbooks/00_validate_render.yml`](playbooks/00_validate_render.yml) | Pre-flight: re-render + run `scripts/validate_configs.py`, surface every check as task output, write `rendered_configs/validation_report.md`, fail the play (and so `site.yml`) if any check fails |
| [`playbooks/01_baseline_build.yml`](playbooks/01_baseline_build.yml) | Platform baseline template -> push -> facts-gathering validation |
| [`playbooks/02_physical_topology.yml`](playbooks/02_physical_topology.yml) | Physical topology template -> push -> LLDP neighbor-count check against `physical_topology.yaml` |
| [`playbooks/03_logical_topology.yml`](playbooks/03_logical_topology.yml) | Logical topology template -> push -> BGP neighbor + endpoint VLAN presence check |
| [`playbooks/site.yml`](playbooks/site.yml) | Runs all three in order |
| [`requirements.yml`](requirements.yml) | `cisco.ios` / `cisco.nxos` / `ansible.netcommon` collections the playbooks need (stages 01-03 only -- `00_validate_render.yml` uses only `ansible.builtin` and talks to no device) |
| [`templates/validation_report.md.j2`](templates/validation_report.md.j2) | Report template `00_validate_render.yml` renders to `rendered_configs/validation_report.md` |

Run with `ansible-playbook playbooks/site.yml` (real push) or add
`-e deploy=false` to render every stage to `rendered_configs/` without
touching a device -- the same dry-run/audit mode
`scripts/render_configs.py` provides, just via real Ansible instead of the
standalone script. The render path (set_fact / include_vars /
`lookup('template', ...)` through this same filter_plugins module) was
verified against `scripts/render_configs.py`'s own output across all 12
devices before being written here -- byte-identical.

`site.yml` runs `00_validate_render.yml` first and stops there (an
`import_playbook` sequence aborts on a failed prior play) if it fails --
verified by temporarily breaking a template's hostname line and confirming
the play failed with `12 check(s) failed` and a non-zero exit code before
restoring it. Add `-e validate_verbose=true` to also print every individual
check as its own task result, not just the per-device rollup and generated
report.

FINDING -- `inventory/hosts.yml`'s `ansible_host` values are each device's
Loopback0 ("management" type) address from `logical_topology.yaml`. That
loopback doesn't exist until Stage 3 configures it, and neither
`physical_topology.yaml` nor `physical_topology_management_network.yaml`
assigns a per-device OOB management IP anywhere (the OOB yaml only maps
console/mgmt ports to terminal-server/mgmt-switch ports, never an IP) --
so there's no data in this repo to build a real day-0-safe inventory from.
This inventory is only valid for a BAU/re-run against a fabric that has
already completed one full build cycle; a real day-0 bring-up needs that
OOB IPAM gap filled in first.

### Config Output
<details>
<summary>abc-hq-wan-01.cfg</summary>
  
```code

! ============================================================
! abc-hq-wan-01  (platform: catalyst8000, role: wan-edge)
! Rendered: baseline -> physical topology -> logical topology
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
! NOTE: no syslog servers defined -- add before deploying
!
snmp-server community CAMPUS-MONITORING-RO RO
snmp-server contact netops@campus.example.net
snmp-server location abc-hq
snmp-server host 10.254.1.20 traps
!
! NOTE: no TACACS+ servers defined -- falling back to local-only authentication (login local, above)
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
```

</details>

<details>
<summary>abc-hq-f01-acc-01.cfg (Layer 3 Routed Access / EVPN-VXLAN VTEP example)</summary>

```code
! ============================================================
! abc-hq-f01-acc-01  (platform: catalyst9000, role: access-vtep)
! Rendered: baseline -> physical topology -> logical topology
! ============================================================

! ---------- 1. Platform baseline (catalyst 9000.j2 + access role.yaml) ----------
!
banner login ^C
Authorized Use Only. System activity is logged.
^C
!
ip domain-name campus.example.net
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
! NOTE: no syslog servers defined -- add before deploying
!
snmp-server community CAMPUS-MONITORING-RO RO
snmp-server contact netops@campus.example.net
snmp-server location abc-hq
snmp-server host 10.254.1.20 traps
!
! NOTE: no TACACS+ servers defined -- falling back to local-only authentication (login local, above)
!
no ip source-route
ip icmp rate-limit unreachable 100
!
! NOTE: accept_redirects, proxy_arp, mask_requests, and ipv6_hardening.
! ra_suppress are per-interface -- deferred to the interface-stage template.
!
dot1x system-auth-control
dot1x critical eapol
! NOTE: fallback restricted_vlan (998)
! is applied per-interface ("authentication event fail action authorize
! vlan <n>" / "authentication event no-response action authorize vlan <n>")
! once interfaces exist -- but see the header finding: VLAN
! 998 isn't in
! the site's VLAN catalog. Confirm the correct value (999?) before this is
! wired into the interface stage.
dot1x timeout reauth-period 300
! NOTE: this sets the global default reauth timer; host_mode ("multi-domain")
! itself is a per-interface setting, deferred.
!
! NOTE: port_security (max 2 MAC(s)/port,
! violation action "protect") has no global
! enable on IOS-XE -- "switchport port-security ..." only exists under
! interface config. Fully deferred to the interface stage.
!
ip dhcp snooping
! NOTE: "ip dhcp snooping vlan <list>" also needs the site's VLAN list
! (logical_topology.yaml's vni_service_mappings: 10,20,30,40,50,999) --
! not rendered here since this stage has no topology data. trust_uplinks_
! to_transit (True) is per-interface
! ("ip dhcp snooping trust"), deferred.
!
! NOTE: "ip arp inspection vlan <list>" needs the same site VLAN list as
! DHCP snooping above -- not rendered here for the same reason.
!
! NOTE: storm_control (broadcast_pps/multicast_pps: 500/500,
! action: "trap_and_log") is entirely per-interface on
! IOS-XE ("storm-control broadcast level pps ...") -- deferred. See header
! finding #2: reconcile against endpoint_services.yaml's conflicting
! percent-based storm_control before this reaches the interface stage.
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
!
ip access-list extended COPP-ACL-TRANSIT_TRAFFIC
 remark ICMP hardware-forwarding-exception traffic (unreachables/TTL-exceeded
 remark generation -- icmp_standards.unreachable_rate_limit is always set in
 remark this baseline). ARP is matched separately below via "match protocol
 remark arp" since ARP isn't an IP protocol an ACL can match. This is a
 remark standard CoPP classification pairing, not a value logical_topology.
 remark yaml / platform_access_baseline.yaml specifies.
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
  ! priority tier from platform_access_baseline: "medium" -- rate above is a starting-point placeholder, tune per site
 class COPP-MANAGEMENT_ACCESS
  police 8000 conform-action transmit exceed-action drop
  ! priority tier from platform_access_baseline: "low" -- rate above is a starting-point placeholder, tune per site
 class COPP-TRANSIT_TRAFFIC
  police 128000 conform-action transmit exceed-action drop
  ! priority tier from platform_access_baseline: "high" -- rate above is a starting-point placeholder, tune per site
!
control-plane
 service-policy input CONTROL-PLANE-POLICY
!
! NOTE: this baseline has no routing_baseline.bgp_security section (see
! header finding #3), even though access-VTEPs speak BGP per
! logical_topology.yaml -- nothing to render here as a result; confirm
! whether that's intentional before the BGP/interface stage is built.
!
! NOTE: secure_boot_verification -- Secure Boot on Catalyst 9300 is a
! hardware-anchored (SUDI-based) feature verified automatically at boot;
! there is no standard IOS-XE enable/disable command for it, so no CLI is
! emitted here. Confirm via 'show platform sudi certificate' post-deploy.
! NOTE: environmental_monitoring -- fan/power/temperature monitoring runs
! by default in hardware (visible via 'show environment all'); there's no
! single enable command for the monitoring itself. If threshold alerting is
! wanted, that's normally SNMP environmental traps, which depend on the
! snmp trap_destinations configured above -- not rendered here since it's
! a separate decision from "monitoring exists."
!
! NOTE: unused_edge_ports (mode: access, default_vlan:
! 999, shutdown: True)
! and underlay_uplinks.link_aggregation (protocol: lacp,
! mode: active) are both per-interface
! -- deferred to the interface-stage template. Unlike NX-OS, IOS-XE needs no
! global "feature lacp"-style command, so there is nothing device-wide to
! render for link aggregation at this stage.
!
end
! ---------- 2. Physical topology (physical topology.j2) ----------
!
hostname abc-hq-f01-acc-01
!
interface TenGigabitEthernet1/1/1
 description FABRIC - to abc-hq-agg-01 TenGigabitEthernet1/0/1 (agg_to_access)
 no switchport
! NOTE: physical_topology.yaml names this port "TenGigabitEthernet1/1/1" (the
! agg_to_access link_standard is 10Gbps), but logical_topology.yaml's
! evpn_vtep.interfaces entry for this same link on abc-hq-f01-acc-01 names
! it "HundredGigabitEthernet..." -- a 100Gbps interface name. The two
! models disagree on both the interface identifier and the implied port
! speed for the identical physical link. Rendered here under the name
! physical_topology.yaml gives, since design.md's Data Models table states
! that model is the "ground-truth inventory... devices, ports,
! interconnects" -- but this needs correcting in logical_topology.yaml (or
! here, if physical_topology.yaml is the one that's stale) before deploying
! for real.
 no shutdown
!
interface TenGigabitEthernet1/1/2
 description FABRIC - to abc-hq-agg-02 TenGigabitEthernet1/0/1 (agg_to_access)
 no switchport
! NOTE: physical_topology.yaml names this port "TenGigabitEthernet1/1/2" (the
! agg_to_access link_standard is 10Gbps), but logical_topology.yaml's
! evpn_vtep.interfaces entry for this same link on abc-hq-f01-acc-01 names
! it "HundredGigabitEthernet..." -- a 100Gbps interface name. The two
! models disagree on both the interface identifier and the implied port
! speed for the identical physical link. Rendered here under the name
! physical_topology.yaml gives, since design.md's Data Models table states
! that model is the "ground-truth inventory... devices, ports,
! interconnects" -- but this needs correcting in logical_topology.yaml (or
! here, if physical_topology.yaml is the one that's stale) before deploying
! for real.
 no shutdown
!
!
end
! ---------- 3. Logical topology (logical topology.j2) ----------
!
interface Loopback0
 ip address 10.3.0.1 255.255.255.255
 description LOOPBACK - management
 no shutdown
!
interface Loopback1
 ip address 10.128.1.1 255.255.255.255
 description LOOPBACK - vtep-source
 no shutdown
!
! NOTE: catalyst9000 has no routing_baseline.bgp_security section in its
! platform baseline yaml (platform_access_baseline.yaml has none at all --
! see catalyst 9000.j2's own header finding #3), yet this device speaks
! BGP per logical_topology.yaml. Neighbors below carry no ttl-security /
! password lines as a result -- confirm whether that's intentional.
interface HundredGigabitEthernet1/1/1
 ip address 10.24.1.1 255.255.255.254
 description FD-A L3 Underlay to agg-01
!
interface HundredGigabitEthernet1/1/2
 ip address 10.24.1.3 255.255.255.254
 description Cross-Plane L3 Underlay to agg-02
!
router bgp 65100
 bgp router-id 10.3.0.1
 bgp log-neighbor-changes
 neighbor 10.24.1.0 remote-as 65100
 neighbor 10.24.1.0 description iBGP Underlay up to agg-01 (FD-A Master)
 neighbor 10.24.1.2 remote-as 65100
 neighbor 10.24.1.2 description iBGP Underlay cross up to agg-02
 address-family ipv4 unicast
  neighbor 10.24.1.0 activate
  neighbor 10.24.1.2 activate
 exit-address-family
!
vrf definition VRF-CAMPUS-USERS
 rd 10.3.0.1:10
 address-family ipv4
  route-target import 65100:10
  route-target export 65100:10
 exit-address-family
!
vlan configuration 10
 member vni 10
!
interface vlan10
 description Campus_Users - Primary user network segment
 vrf forwarding VRF-CAMPUS-USERS
 ip address 10.10.10.1 255.255.255.0
 no ip redirects
 fabric forwarding mode anycast-gateway
 ip helper-address 10.10.100.1
 no shutdown
!
vlan configuration 20
 member vni 20
!
! NOTE: VNI 20 (Security_Cameras) has no anycast_gateway_ip /
! vrf_name in logical_topology.yaml (only vni_id, vlan_id, name,
! description were ever supplied for it -- see that file's own header
! comment). Rendered as an L2-only VNI extension with no SVI/anycast
! gateway; confirm whether it's meant to stay L2-only (plausible for
! Security_Cameras/Voice/Wireless-Mgmt/IPTV/Critical-Services) or is
! simply incomplete data.
vlan configuration 30
 member vni 30
!
! NOTE: VNI 30 (Voice_VoIP) has no anycast_gateway_ip /
! vrf_name in logical_topology.yaml (only vni_id, vlan_id, name,
! description were ever supplied for it -- see that file's own header
! comment). Rendered as an L2-only VNI extension with no SVI/anycast
! gateway; confirm whether it's meant to stay L2-only (plausible for
! Security_Cameras/Voice/Wireless-Mgmt/IPTV/Critical-Services) or is
! simply incomplete data.
vlan configuration 40
 member vni 40
!
! NOTE: VNI 40 (Wireless_AP_Mgmt) has no anycast_gateway_ip /
! vrf_name in logical_topology.yaml (only vni_id, vlan_id, name,
! description were ever supplied for it -- see that file's own header
! comment). Rendered as an L2-only VNI extension with no SVI/anycast
! gateway; confirm whether it's meant to stay L2-only (plausible for
! Security_Cameras/Voice/Wireless-Mgmt/IPTV/Critical-Services) or is
! simply incomplete data.
vlan configuration 50
 member vni 50
!
! NOTE: VNI 50 (IPTV_Multicast) has no anycast_gateway_ip /
! vrf_name in logical_topology.yaml (only vni_id, vlan_id, name,
! description were ever supplied for it -- see that file's own header
! comment). Rendered as an L2-only VNI extension with no SVI/anycast
! gateway; confirm whether it's meant to stay L2-only (plausible for
! Security_Cameras/Voice/Wireless-Mgmt/IPTV/Critical-Services) or is
! simply incomplete data.
vlan configuration 999
 member vni 999
!
! NOTE: VNI 999 (Critical_Services) has no anycast_gateway_ip /
! vrf_name in logical_topology.yaml (only vni_id, vlan_id, name,
! description were ever supplied for it -- see that file's own header
! comment). Rendered as an L2-only VNI extension with no SVI/anycast
! gateway; confirm whether it's meant to stay L2-only (plausible for
! Security_Cameras/Voice/Wireless-Mgmt/IPTV/Critical-Services) or is
! simply incomplete data.
!
interface nve1
 source-interface Loopback1
 host-reachability protocol bgp
 member vni 10 vrf VRF-CAMPUS-USERS
 member vni 20
  ingress-replication protocol bgp
 member vni 30
  ingress-replication protocol bgp
 member vni 40
  ingress-replication protocol bgp
 member vni 50
  ingress-replication protocol bgp
 member vni 999
  ingress-replication protocol bgp
 no shutdown
!
router bgp 65100
 address-family l2vpn evpn
! NOTE: no neighbor is activated under this address-family -- see header
! FINDING 3. Nothing in logical_topology.yaml defines an EVPN overlay
! peer (route-reflector or full-mesh) between access-VTEPs; the two
! underlay iBGP peers above only carry the IPv4 underlay, not L2VPN EVPN.
! member vni configuration above is inert until this is resolved.
!
end
```
</details>

All 12 devices' rendered configuration (baseline + physical topology + logical topology, chained per design.md's Step 1 build workflow) are under [`rendered_configs/`](rendered_configs/) -- one `<hostname>.cfg` file per device: abc-hq-wan-01/02, abc-hq-cor-01..04, abc-hq-agg-01..04, abc-hq-f01-acc-01/02. Generated by [`scripts/render_configs.py`](scripts/render_configs.py), which chains each device's platform baseline template with [physical topology.j2](templates/physical%20topology.j2) and [logical topology.j2](templates/logical%20topology.j2) using the lookup filters in [`filter_plugins/netascode_filters.py`](filter_plugins/netascode_filters.py). Several data-model inconsistencies surfaced while building these two templates and are flagged inline (as `! NOTE` comments) rather than silently resolved -- see the templates' own header comments and the chat analysis for the full list.

### Validation Reports

`scripts/validate_configs.py` output against the current
`rendered_configs/` (run with `python3 scripts/validate_configs.py .` from
the repo root):

```code
DEVICE                PASS  FAIL  SKIP*
----------------------------------------
abc-hq-wan-01           27     0      1
abc-hq-wan-02           27     0      1
abc-hq-cor-01           35     0      0
abc-hq-cor-02           35     0      0
abc-hq-cor-03           35     0      0
abc-hq-cor-04           35     0      0
abc-hq-agg-01           35     0      0
abc-hq-agg-02           35     0      0
abc-hq-agg-03           35     0      0
abc-hq-agg-04           35     0      0
abc-hq-f01-acc-01       41     0      0
abc-hq-f01-acc-02       41     0      0
----------------------------------------
TOTAL                  416     0      2
(*SKIP = known, already-documented data-model gap -- not a render defect)

PASS: 416 checks passed, 0 failed, 2 known-gap skips, across 12 devices
```

SKIP (2, one per WAN router) is FINDING 1 from
[logical topology.j2](templates/logical%20topology.j2)'s own header: a WAN
router's eBGP peer has no IP this repo's data model can derive (the
neighbor IP itself is known from `logical_topology.yaml`, but *which local
interface/IP* it rides on isn't stated anywhere and isn't guessable) -- the
check is intentionally skipped rather than failed, since failing it would
just be re-reporting a data-model gap this doc already documents elsewhere,
not a new render defect.

This validator was itself checked for false positives before being trusted:
a copy of `rendered_configs/abc-hq-cor-01.cfg` was deliberately corrupted
(hostname line truncated/altered, and separately a physical-interface
description swapped onto the wrong interface) and re-run -- both faults
were caught and reported by name/line, confirming the checks are scoped to
the right interface stanza and require an exact line match rather than a
loose substring-anywhere-in-the-file match (an earlier draft of this script
had exactly that bug: `"hostname abc-hq-cor-01" in cfg_text` still matched
a corrupted `hostname abc-hq-cor-01-TYPO` line, since the good string is a
substring of the bad one). The corrupted file was restored and re-verified
byte-identical to the original before this report was captured.

This same check now also runs as
[`playbooks/00_validate_render.yml`](playbooks/00_validate_render.yml) (see
[Ansible Playbooks](#ansible-playbooks)) -- `ansible-playbook
playbooks/00_validate_render.yml` re-renders every device, runs this
script, prints a summary task result giving the pass/fail/skip counts, and
writes the full per-check breakdown to
`rendered_configs/validation_report.md` (one Markdown table per device --
every category/expectation/result this script produced, not just the
summary). Add `-e validate_verbose=true` to also print each individual
check as its own Ansible task result while the play runs. Unlike invoking
the script directly, the playbook turns a failure into a hard gate: it's
the first play `site.yml` imports, and `import_playbook` aborts the whole
sequence if it fails, so a template/filter regression can never reach a
real device push. That gate was verified the same way as the checks above
-- temporarily breaking `templates/physical topology.j2`'s hostname line
reproduced a 12-failure run (one per device) and a non-zero
`ansible-playbook` exit code, confirming `site.yml` would stop before
`01_baseline_build.yml` ever ran; the template was then restored and
re-verified byte-identical, and a clean re-run confirmed 416/0/2 again.
