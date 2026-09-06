# Automation Native Network Design Explain

This is a sample network design to demonstrate how an automation native network design should look like. Automation native is a design approach which incorporates the elements required by network automation into design process. These elements are: Determinsitic Topology, Abstraction, Machine-Friendly interfaces & structured data, Unique source of truth, Declarative state and Streaming Telemetry.

Key takeaways:
- Data model first, design content is generated from vaarious data models in yaml.
- Generated contents includes diagrams, cable patching matrix, design specific templates (And device template which is not part of this design), playbooks
- Data model is constructed from various schema by merging the values obtained from source of truth (i.e Netbox). The integration ioof SOT s not shown in this example.
- Design is validated by comparing the config output with the data model.
- Concept:
  - schema + value = data model
  - data model + template = config
  - playbook + config = deployed config
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

| Data Model | Purpose | JSON Schema |
|---|---|---|
| [Physical Topology - Campus Network](models/physical%20topology.yaml) | Ground-truth inventory of campus network hardware and cabling — devices, ports, and interconnects. | [physical-topology.schema.json](schemas/physical-topology.schema.json) |
| [Physical Topology - Management Network](models/physical%20topology%20management%20network.yaml) | Ground-truth inventory of the OOB management network — terminal servers, management switches, and console cabling. | [physical-topology-management-network.schema.json](schemas/physical-topology-management-network.schema.json) |
| [Logical Topology](models/logical%20topology.yaml) | Defines the campus's BGP underlay and VXLAN EVPN overlay — how traffic is forwarded and isolated, independent of physical hardware. | [logical-topology.schema.json](schemas/logical-topology.schema.json) |
| [Endpoint Service](models/endpoint%20service.yaml) | Standardized security and QoS baseline for endpoint switchports — loop protection, 802.1X/MAB, FHS, and edge QoS | [endpoint-service.schema.json](schemas/endpoint-service.schema.json) |

### Device Role Models

A role is the function of the device performed in the design. Device role models define a standardized, platform-agnostic set of foundational hardening and operational features that must be implemented on a role (i.e. WAN Edge). It is intentionally decoupled from the hardware platform such that to allow flexible use of platform against role. These models will be used in conjunction with the platform specific jinja2 template to render the configuration output that is required by the platform acting as that role.

| Role-based Data Model | Platform Template| JSON Schema |
|---|---|---|
| [WAN Edge Role](models/wan%20edge%20role.yaml) | [Catalyst 8000](templates/catalyst%208000.j2) | [wan-edge-role.schema.json](schemas/wan-edge-role.schema.json) |
| [Core & Agg Role](models/core%20agg%20role.yaml) | [Nexus 93240](templates/nexus%2093240.j2) | [core-agg-role.schema.json](schemas/core-agg-role.schema.json) |
| [Access Role](models/access%20role.yaml) | [Catalyst 9000](templates/catalyst%2090000.j2) | [access-role.schema.json](schemas/access-role.schema.json) |

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

### Step 6. Execute [service deployment playbook](ansible_resources/playbooks/bau_endpoint_provisioning.yml) to provision the interface on the access switch.

```yaml
ansible-playbook playbooks/bau_endpoint_provisioning.yml \
    -e switch_name=abc-hq-f01-acc-01 -e interface_name=GigabitEthernet1/0/5 \
    -e vlan=20 -e voice_vlan=30 -e description="Marketing desk move, INC0012345"
```



