# Automation Native Campus Network Design

This is a sample network design to demonstrate how an automation native network design should look like. Automation native is a design approach which incorporates the elements required by network automation into design process. These elements are: Determinsitic Topology, Abstraction, Machine-Friendly interfaces & structured data, Unique source of truth, Declarative state and Streaming Telemetry.

Key steps:
- Design created from data model in yaml
- Diagram rendered from yaml

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

![Campus Network Diagram](./topology1.svg)

![Campus Management Network Diagram](./mgmt_topology.svg)

### Control Plane & Overlay Architecture

* Deploys a unified BGP and Segment Routing-based transport underlay.
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

## Schemas & Models

This design is constructed from a set of data schemas which provides a structured "source of truth" information that the automation tools will need. The data schemas are used to render, validate, deploy and maintainthe configurations over automated workflows.

| Data Models | Purpose & Applications | Schema |
|---|---|---|
| Physical Topology - Campus Network | | |
| Physical Topology - Management Network | | |
| Logical Topology | | |
| WAN Routers Baseline | | |
| Core & Agg Switches Baseline | | |
| Access Switches Baseline | | |

## Deployment Details

Physical data model to generate rack & stack, patching scheme. The data model also need to include rack information.
Onsite facility team complete the rack and stack, patching, preconfigure with mgmt IP so that Ansible runner is reachable.
Device build steps.
Device specific baseline configuration
- Data model for each platform for baseline configuration, data model is schema only, data is pulled from the network source of truth, Jinja2 template per device platform to render, Ansible to deploy
Design specific configuration
- Use data model from physical topology and logical topology.


## Reference

### Data Models
<details>
<summary>Physical Topology - Campus Network </summary>
  
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

<details>
<summary>Logical Topology</summary>

```yaml

# ============================================================================
# Site Routing, BGP, & VXLAN EVPN Complete Data Model Contract
# Update: LAYER 3 ROUTED ACCESS VTEPS ONLY (Campus unified AS 65100)
# Expanded EVPN Overlay VNI Mappings (Data, Voice, Wireless APs, IPTV, Critical)
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
    # Overlay is running exclusively on Access Tier
    vtep_parameters:
      nve_interface: "NVE1"
      vtep_source_interface: "Loopback1"
    vni_service_mappings:
      # Logical services mapped to L3 access
      - vni_id: 10
        vlan_id: 10
        name: "Campus_Users"
        description: "Primary user network segment"
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
    - name: "abc-hq-cor-01"
      failure_domain: "FD-A"
      routing:
        global: { bgp_asn: 65100, router_id: "10.1.0.1" }
        loopbacks: [{ interface: "Loopback0", ip_address: "10.1.0.1/32", type: "management" }]
        interfaces:
          - { interface: "HundredGigE0/1", ip_address: "10.18.1.1/31" } # to wan-01
          - { interface: "HundredGigE1/1", ip_address: "10.9.1.0/31" } # to agg-01
        bgp_peers:
          - { description: "iBGP Underlay to wan-01", peer_ip: "10.18.1.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay to agg-01", peer_ip: "10.9.1.1", remote_as: 65100, type: "ibgp" }
    # [...Other cores 02, 03, 04 omitted for brevity...]

    # --------------------------------------------------------------------------
    # LAYER 3: AGGREGATION SWITCHES (PURE L3 UNDERLAY TRANSIT)
    # --------------------------------------------------------------------------
    - name: "abc-hq-agg-01"
      failure_domain: "FD-A"
      role: "aggregation-transit"
      # Pure Underlay Transit - No VTEP / No EVPN overlay termination
      routing:
        global: { bgp_asn: 65100, router_id: "10.2.0.1" }
        loopbacks:
          - { interface: "Loopback0", ip_address: "10.2.0.1/32", type: "management" }
        interfaces:
          - { interface: "HundredGigE0/1", ip_address: "10.9.1.1/31" } # Up to cor-01
          - { interface: "HundredGigE0/4", ip_address: "10.24.1.0/31" } # Down to f01-acc-01
        bgp_peers:
          - { description: "iBGP Underlay Up to cor-01", peer_ip: "10.9.1.0", remote_as: 65100, type: "ibgp" }
          - { description: "iBGP Underlay Down to f01-acc-01", peer_ip: "10.24.1.1", remote_as: 65100, type: "ibgp" }
    # [...Other aggs 02, 03, 04 omitted for brevity...]

    # --------------------------------------------------------------------------
    # LAYER 4: LAYER 3 ROUTED ACCESS VTEPS (Floors 1-10)
    # Target Switch Type: e.g., Cisco Catalyst 9300 / Arista 720XP
    # --------------------------------------------------------------------------
    floors:
      - floor_number: 1
        access_vteps:
          - name: "abc-hq-f01-acc-01"
            failure_domain: "FD-A"
            role: "access-vtep" # Defining Routed Access VTEP
            evpn_vtep:
              global: { bgp_asn: 65100, router_id: "10.3.0.1" }
              loopbacks:
                - { interface: "Loopback0", ip_address: "10.3.0.1/32", type: "management" }
                - { interface: "Loopback1", ip_address: "10.128.1.1/32", type: "vtep-source" } # Unique VTEP Source per Switch
              interfaces:
                - interface: "HundredGigabitEthernet1/1/1"
                  description: "FD-A L3 Underlay to agg-01"
                  ip_address: "10.24.1.1/31" # FD-A Routed Access IPAM
                - interface: "HundredGigabitEthernet1/1/2"
                  description: "Cross-Plane L3 Underlay to agg-02"
                  ip_address: "10.24.1.3/31" # Cross-Plane Routed Access IPAM
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
                  ip_address: "10.24.2.1/31" # FD-B Routed Access IPAM
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

      # [...Floors 2-10 are repetitive using the acc-vtep schema shown above...]
```
</details>
