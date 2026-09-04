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
    <img src="automation-native-data-model-pipeline.svg" width="1200">
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

![Campus Network Diagram](./topology1.svg)

![Campus Management Network Diagram](./mgmt_topology.svg)

### Control Plane & Overlay Architecture

* Deploys a unified BGP Routing-based transport underlay.
* Runs EVPN-VXLAN on top of the underlay to deliver flexible Layer 2/Layer 3 multi-tenant virtual overlay networks.

![Logical Network Diagram](./logical.svg)

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

### Design Specific Models

| Data Model | Purpose |
|---|---|
| Physical Topology - Campus Network | Define the precise real-world composition and interconnection of network hardware, including devices, modules, ports, and cables, providing the ground-truth asset and connectivity inventory for the network |
| Physical Topology - Management Network | Define the precise real-world composition and interconnection of the dedicated out-of-band (OOB) hardware—including management switches, terminal servers, console/management ports, and all associated cabling |
| Logical Topology | Define the abstract, software-defined architecture of the network—including routing domains (BGP AS), overlay networks (VXLAN EVPN), virtual network functions, and service paths—that operates independently of the underlying physical hardware, detailing how traffic is controlled, isolated, and forwarded |
| Endpoint Service | Define the granular physical port configurations, Layer 2 loop protections, First-Hop Security (FHS) controls, 802.1X/MAB identity profiles, and edge QoS policies facing client devices, establishing a standardized, secure link-level baseline across all endpoint switchports |

### Device Baseline Models

Device Baseline Data Model is to define a standardized, vendor-agnostic set of foundational hardening, security, and operational features that must be implemented on every network device, regardless of its specific role or placement within the network architecture. This model will be used in conjunction with a platform specific template to render the configuration output required by the platform.

Based on the platform of choices, the following models will be used by this design.

| Model | Platform | Use Case |
|---|---|---|
| Edge Device Model | Vendor A xxx | Campus WAN routers |
| Core Device Model | Vendor B xxx | Core & Aggregration switches |
| Access Device Model | Vendor C xxx | Access switches |

## Deployment Details

### A. Management Network Build

Prerequisite:
- 
- 
- Configure

### B. Campus Network Build

Prerequisite:
- Management Network has been up and running so that devices are reachable by Ansible runners
- Devices are physically racked and patched according to the patching scheme

Build workflow:
Apply the baseline template for each device -> Validate device local configuration -> Apply physical topology template -> Run point-to-point connectivity validation between devices -> Apply logical topology template -> Run layer 3 connectivity validation, endpoint vlan validation

| Task | Playbook Name | j2 Template Used | Data model Adopted |
|---|---|---|---|
| Baseline config build | baseline-build playbook | J2 template name | Access Switch Platform Baseline |
| Baseline validation | baseline-validation playbook | - | Corresponding platform baseline model |
| Physical topology build | physical-build playbook | J2 template name | physical topology |
| Physical validation | physical-validation playbook | - | physical topology |
| Logical topology build | logical-build playbook | J2 template name | logical topology |
| Logical validation | logical-validation playbook | - | logical topology |


Physical data model to generate rack & stack, patching scheme. The data model also need to include rack information.
Onsite facility team complete the rack and stack, patching, preconfigure with mgmt IP so that Ansible runner is reachable.
Device build steps.
Device specific baseline configuration
- Data model for each platform for baseline configuration, data model is schema only, data is pulled from the network source of truth, Jinja2 template per device platform to render, Ansible to deploy
Design specific configuration
- Use data model from physical topology and logical topology.

## References

### Data Models
<details>
<summary>Physical Topology - Campus Network </summary>
  
```yaml
site_physical_topology:
  site_code: "abc-hq"
  site_name: "Company ABC Main Campus"
  building: "Main Building (10 Floors)"

  # ============================================================================
  # 1. FAILURE DOMAIN & RACK INFRASTRUCTURE DEFINITIONS
  # ============================================================================
  failure_domains:
    - domain_id: "FD-A"
      description: "Primary Redundancy Plane (Red Domain)"
      rack_group: "Suite-A / Left-IDF"
      racks:
        - rack_id: "RACK-A01"
          location: "Main Equipment Room - Row A, Rack 1"
          u_space_total: 42
          mounted_devices:
            - name: "abc-hq-wan-01"
              u_position_start: 40
              u_height: 2
            - name: "abc-hq-cor-01"
              u_position_start: 36
              u_height: 2
            - name: "abc-hq-cor-02"
              u_position_start: 34
              u_height: 2
            - name: "abc-hq-agg-01"
              u_position_start: 30
              u_height: 2
        - rack_id: "RACK-A02"
          location: "Main Equipment Room - Row A, Rack 2"
          u_space_total: 42
          mounted_devices:
            - name: "abc-hq-agg-02"
              u_position_start: 30
              u_height: 2

    - domain_id: "FD-B"
      description: "Secondary Redundancy Plane (Blue Domain)"
      rack_group: "Suite-B / Right-IDF"
      racks:
        - rack_id: "RACK-B01"
          location: "Main Equipment Room - Row B, Rack 1"
          u_space_total: 42
          mounted_devices:
            - name: "abc-hq-wan-02"
              u_position_start: 40
              u_height: 2
            - name: "abc-hq-cor-03"
              u_position_start: 36
              u_height: 2
            - name: "abc-hq-cor-04"
              u_position_start: 34
              u_height: 2
            - name: "abc-hq-agg-03"
              u_position_start: 30
              u_height: 2
        - rack_id: "RACK-B02"
          location: "Main Equipment Room - Row B, Rack 2"
          u_space_total: 42
          mounted_devices:
            - name: "abc-hq-agg-04"
              u_position_start: 30
              u_height: 2

  # ============================================================================
  # 2. GLOBAL LINK SPEED STANDARDS
  # ============================================================================
  link_standards:
    wan_circuit:
      speed: "10Gbps"
      media: "10GBASE-SR_Fiber"
    inter_device: # Same-layer horizontal links (WAN-to-WAN, Core-to-Core, Agg-to-Agg)
      speed: "100Gbps"
      media: "100GBASE-SR4_Fiber"
    core_to_agg:
      speed: "100Gbps"
      media: "100GBASE-SR4_Fiber"
    agg_to_access:
      speed: "10Gbps"
      media: "10GBASE-SR_Fiber"

  # ============================================================================
  # 3. DEVICE INVENTORY & PHYSICAL INTERCONNECTS
  # ============================================================================

  # --- WAN LAYER ---
  wan_routers:
    - name: "abc-hq-wan-01"
      failure_domain: "FD-A"
      rack_location: "RACK-A01"
      external_links:
        - interface: "TenGigabitEthernet0/0/0"
          type: "wan_circuit"
          description: "Service Provider A 10Gbps Ethernet Line"
      internal_links:
        - local_port: "HundredGigE0/1/0"
          remote_device: "abc-hq-wan-02"       # Horizontal WAN Interconnect (FD-A to FD-B)
          remote_port: "HundredGigE0/1/0"
          type: "inter_device"
        - local_port: "HundredGigE0/2/0"
          remote_device: "abc-hq-cor-01"       # FD-A WAN to FD-A Core
          remote_port: "HundredGigE0/0/1"
          type: "inter_device"
        - local_port: "HundredGigE0/2/1"
          remote_device: "abc-hq-cor-03"       # Cross-FD: FD-A WAN to FD-B Core
          remote_port: "HundredGigE0/0/1"
          type: "inter_device"

    - name: "abc-hq-wan-02"
      failure_domain: "FD-B"
      rack_location: "RACK-B01"
      external_links:
        - interface: "TenGigabitEthernet0/0/0"
          type: "wan_circuit"
          description: "Service Provider B 10Gbps Ethernet Line"
      internal_links:
        - local_port: "HundredGigE0/1/0"
          remote_device: "abc-hq-wan-01"       # Horizontal WAN Interconnect (FD-B to FD-A)
          remote_port: "HundredGigE0/1/0"
          type: "inter_device"
        - local_port: "HundredGigE0/2/0"
          remote_device: "abc-hq-cor-04"       # FD-B WAN to FD-B Core
          remote_port: "HundredGigE0/0/1"
          type: "inter_device"
        - local_port: "HundredGigE0/2/1"
          remote_device: "abc-hq-cor-02"       # Cross-FD: FD-B WAN to FD-A Core
          remote_port: "HundredGigE0/0/1"
          type: "inter_device"

  # --- CORE LAYER ---
  core_routers:
    # Failure Domain A Core Pair
    - name: "abc-hq-cor-01"
      failure_domain: "FD-A"
      rack_location: "RACK-A01"
      links:
        - local_port: "HundredGigE0/0/1"
          remote_device: "abc-hq-wan-01"       # Core-to-WAN Uplink
          remote_port: "HundredGigE0/2/0"
          type: "inter_device"
        - local_port: "HundredGigE0/0/2"
          remote_device: "abc-hq-cor-02"       # Core-to-Core (Intra-FD)
          remote_port: "HundredGigE0/0/2"
          type: "inter_device"
        - local_port: "HundredGigE1/0/1"
          remote_device: "abc-hq-agg-01"       # Core-to-Agg
          remote_port: "HundredGigE0/1"
          type: "core_to_agg"
        - local_port: "HundredGigE1/0/2"
          remote_device: "abc-hq-agg-02"       # Core-to-Agg
          remote_port: "HundredGigE0/1"
          type: "core_to_agg"

    - name: "abc-hq-cor-02"
      failure_domain: "FD-A"
      rack_location: "RACK-A01"
      links:
        - local_port: "HundredGigE0/0/1"
          remote_device: "abc-hq-wan-02"       # Core-to-WAN Uplink (Cross-FD)
          remote_port: "HundredGigE0/2/1"
          type: "inter_device"
        - local_port: "HundredGigE0/0/2"
          remote_device: "abc-hq-cor-01"       # Core-to-Core (Intra-FD)
          remote_port: "HundredGigE0/0/2"
          type: "inter_device"
        - local_port: "HundredGigE1/0/1"
          remote_device: "abc-hq-agg-01"       # Core-to-Agg
          remote_port: "HundredGigE0/2"
          type: "core_to_agg"
        - local_port: "HundredGigE1/0/2"
          remote_device: "abc-hq-agg-02"       # Core-to-Agg
          remote_port: "HundredGigE0/2"
          type: "core_to_agg"

    # Failure Domain B Core Pair
    - name: "abc-hq-cor-03"
      failure_domain: "FD-B"
      rack_location: "RACK-B01"
      links:
        - local_port: "HundredGigE0/0/1"
          remote_device: "abc-hq-wan-01"       # Core-to-WAN Uplink (Cross-FD)
          remote_port: "HundredGigE0/2/1"
          type: "inter_device"
        - local_port: "HundredGigE0/0/2"
          remote_device: "abc-hq-cor-04"       # Core-to-Core (Intra-FD)
          remote_port: "HundredGigE0/0/2"
          type: "inter_device"
        - local_port: "HundredGigE1/0/1"
          remote_device: "abc-hq-agg-03"       # Core-to-Agg
          remote_port: "HundredGigE0/1"
          type: "core_to_agg"
        - local_port: "HundredGigE1/0/2"
          remote_device: "abc-hq-agg-04"       # Core-to-Agg
          remote_port: "HundredGigE0/1"
          type: "core_to_agg"

    - name: "abc-hq-cor-04"
      failure_domain: "FD-B"
      rack_location: "RACK-B01"
      links:
        - local_port: "HundredGigE0/0/1"
          remote_device: "abc-hq-wan-02"       # Core-to-WAN Uplink
          remote_port: "HundredGigE0/2/0"
          type: "inter_device"
        - local_port: "HundredGigE0/0/2"
          remote_device: "abc-hq-cor-03"       # Core-to-Core (Intra-FD)
          remote_port: "HundredGigE0/0/2"
          type: "inter_device"
        - local_port: "HundredGigE1/0/1"
          remote_device: "abc-hq-agg-03"       # Core-to-Agg
          remote_port: "HundredGigE0/2"
          type: "core_to_agg"
        - local_port: "HundredGigE1/0/2"
          remote_device: "abc-hq-agg-04"       # Core-to-Agg
          remote_port: "HundredGigE0/2"
          type: "core_to_agg"

  # --- AGGREGATION LAYER ---
  aggregation_switches:
    - name: "abc-hq-agg-01"
      failure_domain: "FD-A"
      rack_location: "RACK-A01"
      links:
        - local_port: "HundredGigE0/48"
          remote_device: "abc-hq-agg-02"       # Agg-to-Agg (Same FD)
          remote_port: "HundredGigE0/48"
          type: "inter_device"

    - name: "abc-hq-agg-02"
      failure_domain: "FD-A"
      rack_location: "RACK-A02"
      links:
        - local_port: "HundredGigE0/48"
          remote_device: "abc-hq-agg-01"       # Agg-to-Agg (Same FD)
          remote_port: "HundredGigE0/48"
          type: "inter_device"

    - name: "abc-hq-agg-03"
      failure_domain: "FD-B"
      rack_location: "RACK-B01"
      links:
        - local_port: "HundredGigE0/48"
          remote_device: "abc-hq-agg-04"       # Agg-to-Agg (Same FD)
          remote_port: "HundredGigE0/48"
          type: "inter_device"

    - name: "abc-hq-agg-04"
      failure_domain: "FD-B"
      rack_location: "RACK-B02"
      links:
        - local_port: "HundredGigE0/48"
          remote_device: "abc-hq-agg-03"       # Agg-to-Agg (Same FD)
          remote_port: "HundredGigE0/48"
          type: "inter_device"

  # --- ACCESS LAYER GENERATOR (Floors 1-10) ---
  floors:
    - floor_number: 1
      access_switches:
        - name: "abc-hq-f01-acc-01"
          failure_domain: "FD-A"
          rack_location: "Floor-01 IDF-A Rack 1"
          uplinks:
            - local_port: "TenGigabitEthernet1/1/1"
              remote_device: "abc-hq-agg-01"
              remote_port: "TenGigabitEthernet1/0/1"
              type: "agg_to_access"
            - local_port: "TenGigabitEthernet1/1/2"
              remote_device: "abc-hq-agg-02"
              remote_port: "TenGigabitEthernet1/0/1"
              type: "agg_to_access"

        - name: "abc-hq-f01-acc-02"
          failure_domain: "FD-B"
          rack_location: "Floor-01 IDF-B Rack 1"
          uplinks:
            - local_port: "TenGigabitEthernet1/1/1"
              remote_device: "abc-hq-agg-03"
              remote_port: "TenGigabitEthernet1/0/1"
              type: "agg_to_access"
            - local_port: "TenGigabitEthernet1/1/2"
              remote_device: "abc-hq-agg-04"
              remote_port: "TenGigabitEthernet1/0/1"
              type: "agg_to_access"

    # [ Floors 2 to 10 follow the identical pattern for acc-01 and acc-02 ]
```
</details>

<details>
<summary>Physical Topology - Device Management Network </summary>

```yaml
management_context:
  site_code: "abc-hq"
  site_name: "Company ABC Main Campus OOB"

  # ============================================================================
  # 1. FAILURE DOMAIN & RACK INFRASTRUCTURE DEFINITIONS
  # ============================================================================
  failure_domains:
    - domain_id: "FD-MGT"
      description: "Out-of-Band Management Redundancy Plane"
      rack_group: "Suite-MGT / OOB Rack Room"
      racks:
        - rack_id: "RACK-MGT01"
          location: "Main Equipment Room - Row MGT, Rack 1"
          u_space_total: 42
          mounted_devices:
            - name: "abc-hq-mgt-wan-01"
              u_position_start: 40
              u_height: 2
            - name: "abc-hq-mgt-cor-01"
              u_position_start: 36
              u_height: 2
            - name: "abc-hq-mgt-ts-idf-main-01"
              u_position_start: 32
              u_height: 2
            - name: "abc-hq-mgt-acc-idf-main-01"
              u_position_start: 30
              u_height: 2

  # ============================================================================
  # 2. MANAGEMENT LINK SPEED STANDARDS
  # ============================================================================
  link_standards:
    mgt_wan_circuit:
      speed: "1Gbps"
      media: "1000BASE-T_Copper"
      description: "Dedicated management WAN connection (console/SSH access)"
    mgt_backbone:
      speed: "10Gbps"
      media: "10GBASE-SR_Fiber"
      description: "Connections between Management Core/Agg/Access switches"
    mgt_ethernet:
      speed: "1Gbps"
      media: "1000BASE-T_Copper"
      description: "Production device Management GigE port to MGT Switch (SSH)"
    mgt_console:
      speed: "115200bps"
      media: "Serial-RJ45"
      description: "Production device Console port to Terminal Server"

  # ============================================================================
  # 3. MANAGEMENT IPAM SCHEMA
  # ============================================================================
  ipam_schema:
    oob_wan_subnet: "192.168.100.0/30" # Dedicated WAN IP space
    oob_management_loopbacks: "10.254.0.0/19" # Loopbacks for OOB switches
    oob_console_servers: "10.254.32.0/24" # Specific for TS nodes

  # ============================================================================
  # 4. SEPARATE MANAGEMENT INVENTORY (Out-of-Band Network)
  # ============================================================================
  management_tier:

    # --- MANAGEMENT WAN LAYER ---
    mgt_wan_routers:
      - name: "abc-hq-mgt-wan-01"
        failure_domain: "FD-MGT"
        rack_location: "RACK-MGT01"
        external_links:
          - interface: "GigabitEthernet0/0/0"
            type: "mgt_wan_circuit"
            description: "Dedicated Management WAN line (OOB Access)"
        internal_links:
          - local_port: "TenGigabitEthernet0/1/0"
            remote_device: "abc-hq-mgt-cor-01"
            remote_port: "TenGigabitEthernet1/1"
            type: "mgt_backbone"

    # --- MANAGEMENT CORE LAYER ---
    mgt_core_switches:
      - name: "abc-hq-mgt-cor-01"
        failure_domain: "FD-MGT"
        rack_location: "RACK-MGT01"
        links:
          # Uplink to MGT WAN
          - local_port: "TenGigabitEthernet1/1"
            remote_device: "abc-hq-mgt-wan-01"
            remote_port: "TenGigabitEthernet0/1/0"
            type: "mgt_backbone"
          # Fiber Backbone down to Management switches in IDFs
          - local_port: "TenGigabitEthernet1/2"
            remote_device: "abc-hq-mgt-acc-idf-main-01" # MGT-Switch (SSH)
            remote_port: "TenGigabitEthernet1/1"
            type: "mgt_backbone"
          - local_port: "TenGigabitEthernet1/3"
            remote_device: "abc-hq-mgt-ts-idf-main-01" # Terminal-Server (Console)
            remote_port: "TenGigabitEthernet1/1"
            type: "mgt_backbone"

    # --- MANAGEMENT ACCESS LAYER (OOB Gateways) ---
    mgt_access_nodes:
      # Terminal Servers for Serial Console access
      - name: "abc-hq-mgt-ts-idf-main-01"
        type: "terminal_server"
        failure_domain: "FD-MGT"
        rack_location: "RACK-MGT01"
        links:
          - local_port: "TenGigabitEthernet1/1"
            remote_device: "abc-hq-mgt-cor-01"
            remote_port: "TenGigabitEthernet1/3"
            type: "mgt_backbone"
        # Definition of physical Async ports connecting to production device Console ports
        async_console_mappings:
          - async_port: "Async1"
            description: "Console to wan-01"
            target_device: "abc-hq-wan-01"
          - async_port: "Async2"
            description: "Console to cor-01"
            target_device: "abc-hq-cor-01"

      # Management Switches for GigE SSH access
      - name: "abc-hq-mgt-acc-idf-main-01"
        type: "mgt_switch"
        failure_domain: "FD-MGT"
        rack_location: "RACK-MGT01"
        links:
          - local_port: "TenGigabitEthernet1/1"
            remote_device: "abc-hq-mgt-cor-01"
            remote_port: "TenGigabitEthernet1/2"
            type: "mgt_backbone"
        # Definition of physical GigE ports connecting to production device Management ports
        mgt_ethernet_mappings:
          - mgt_port: "GigabitEthernet1/1"
            description: "SSH to wan-01 Management0"
            target_device: "abc-hq-wan-01"
          - mgt_port: "GigabitEthernet1/2"
            description: "SSH to cor-01 GigabitEthernet0"
            target_device: "abc-hq-cor-01"
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
# ============================================================================
# Site Endpoint Interface Provisioning Data Model
# Layer 1/2/AAA policy applied to end-user-facing access ports.
#
# Changes made from the version you pasted:
#   1. evpn_overlay_design (vtep_parameters + vni_service_mappings) removed --
#      it duplicated logical_topology.yaml's copy and is now the single
#      table in service_overlay.yaml. This file already referenced VLANs
#      by ID everywhere else (native_vlan, voice_vlan, access_vlan), so no
#      other change was needed to keep that pattern.
#   2. access_switch_baseline.quality_of_service.ingress_policy renamed to
#      ingress_policy_map, to match the field name used in the more
#      detailed endpoint_interfaces.quality_of_service section below --
#      same setting, was two different key names for it.
# ============================================================================

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
<summary>Device Model - Edge Device</summary>
  
```yaml
# ============================================================================
# PLATFORM BASELINE DATA MODEL: WAN ROUTER (Vendor-Agnostic)
# ============================================================================
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
<summary>Device Model - Core Device</summary>
  
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
<summary>Device Model - Access Device</summary>
  
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

### Ansible Playbooks

### Config Output

### Validation Reports

