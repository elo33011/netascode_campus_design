# Automation Native Campus Network Design

This is a sample network design to demonstrate how an automation native network design should look like. Automation native is a design approach which incorporates the elements required by network automation into design process. These elements are: Determinsitic Topology, Abstraction, Machine-Friendly interfaces & structured data, Unique source of truth, Declarative state and Streaming Telemetry.

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

## Network Design

This section outlines the architectural framework and design principles for the campus network:

### Topology & Connectivity Hierarchy

* Implements a standard five-tier architecture: Regional On-Prem/Cloud Colo Access $\rightarrow$ WAN $\rightarrow$ Core $\rightarrow$ Aggregation $\rightarrow$ Access.
* Extends dual-homed connections across all network tiers for end-to-end path redundancy.

### Control Plane & Overlay Architecture

* Deploys a unified BGP and Segment Routing-based transport underlay.
* Runs EVPN-VXLAN on top of the underlay to deliver flexible Layer 2/Layer 3 multi-tenant virtual overlay networks.

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

### Data models 

<details>
<summary>Physical Topology</summary>

```yaml
---
site_physical_topology:
  site_code: "abc-hq"
  site_name: "Company ABC Main Campus"
  building: "Main Building (10 Floors)"

  # ============================================================================
  # 1. FAILURE DOMAIN DEFINITIONS
  # ============================================================================
  failure_domains:
    - domain_id: "FD-A"
      description: "Primary Redundancy Plane (Red Domain)"
      rack_group: "Suite-A / Left-IDF"
    - domain_id: "FD-B"
      description: "Secondary Redundancy Plane (Blue Domain)"
      rack_group: "Suite-B / Right-IDF"

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
      links:
        - local_port: "HundredGigE0/48"
          remote_device: "abc-hq-agg-02"       # Agg-to-Agg (Same FD)
          remote_port: "HundredGigE0/48"
          type: "inter_device"

    - name: "abc-hq-agg-02"
      failure_domain: "FD-A"
      links:
        - local_port: "HundredGigE0/48"
          remote_device: "abc-hq-agg-01"       # Agg-to-Agg (Same FD)
          remote_port: "HundredGigE0/48"
          type: "inter_device"

    - name: "abc-hq-agg-03"
      failure_domain: "FD-B"
      links:
        - local_port: "HundredGigE0/48"
          remote_device: "abc-hq-agg-04"       # Agg-to-Agg (Same FD)
          remote_port: "HundredGigE0/48"
          type: "inter_device"

    - name: "abc-hq-agg-04"
      failure_domain: "FD-B"
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

![Campus Network Diagram](./topology1.svg)

<details>
<summary>Physical Topology - Device Management Network </summary>

```yaml
# ============================================================================
# Site Out-of-Band (OOB) Management Data Model Contract
# Target: Campus Management Pipeline (Console/SSH Access, separate from SOT)
# ============================================================================

management_context:
  site_code: "abc-hq"
  site_name: "Company ABC Main Campus OOB"

  # ============================================================================
  # 1. MANAGEMENT LINK SPEED STANDARDS
  # ============================================================================
  # Global standards specifically for OOB management connectivity.
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
  # 2. MANAGEMENT IPAM SCHEMA (Examples)
  # ============================================================================
  ipam_schema:
    oob_wan_subnet: "192.168.100.0/30" # Dedicted WAN IP space
    oob_management_loopbacks: "10.254.0.0/19" # Loopbacks for OOB switches
    oob_console_servers: "10.254.32.0/24" # Specific for TS nodes

  # ============================================================================
  # 3. SEPARATE MANAGEMENT INVENTORY (Out-of-Band Network)
  # ============================================================================
  # This dedicated network provides secure console and SSH access to the designs.
  management_tier:

    # --- MANAGEMENT WAN LAYER ---
    mgt_wan_routers:
      - name: "abc-hq-mgt-wan-01"
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

![Campus Network Diagram](./mgmt_topology.svg)
