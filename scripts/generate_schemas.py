#!/usr/bin/env python3
"""
Generates a JSON Schema (draft 2020-12) for every data model YAML in
models/, for reference: what shape does each data model actually have,
which fields are always present vs. optional, and what are the known
closed vocabularies (link types, BGP peer types, CoPP priority tiers, ...).

This is inferred structurally from the YAML itself (every scalar, object,
and array actually present is walked; a field is "required" only if every
sibling entry in its list has it, so a data-model gap -- e.g. VNI 20-50
lacking anycast_gateway_ip -- shows up as the field being optional, not as
a fabricated default), then a small, explicit OVERRIDES table adds the
handful of things structural inference cannot know on its own: enums for
closed vocabularies, human descriptions/titles, and a few nullable-field
type corrections. Nothing in OVERRIDES invents new structure -- every
override patches a property this script already found.

Regenerate anytime a models/*.yaml file changes:
  python3 scripts/generate_schemas.py <repo_root>

Usage: generate_schemas.py <repo_root>
"""
import sys
import os
import re
import json
import yaml

IPV4_RE = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
IPV4_CIDR_RE = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$')

SCHEMA_ID_BASE = "https://schemas.abc-hq.example.net/netascode-campus"  # DEMO placeholder -- not a real host

# ============================================================================
# Structural inference: YAML value -> JSON Schema fragment, with merging
# across sibling list items (union of properties, intersection of required)
# ============================================================================

def infer_string_schema(s):
    schema = {"type": "string"}
    if IPV4_CIDR_RE.match(s):
        schema["pattern"] = IPV4_CIDR_RE.pattern
        schema["description"] = "IPv4 address in CIDR notation (address/prefix-length)."
    elif IPV4_RE.match(s):
        schema["pattern"] = IPV4_RE.pattern
        schema["description"] = "IPv4 address, no prefix length."
    return schema


def infer_schema(value):
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return infer_string_schema(value)
    if isinstance(value, list):
        return infer_array_schema(value)
    if isinstance(value, dict):
        return infer_object_schema(value)
    return {}


def infer_object_schema(d):
    props = {}
    for k, v in d.items():
        props[k] = infer_schema(v)
    return {
        "type": "object",
        "properties": props,
        "required": list(props.keys()),
        "additionalProperties": False,
    }


def infer_array_schema(lst):
    if not lst:
        return {"type": "array", "items": {}}
    item_schema = None
    for item in lst:
        s = infer_schema(item)
        item_schema = s if item_schema is None else merge_schema(item_schema, s)
    return {"type": "array", "items": item_schema}


def _type_set(t):
    if t is None:
        return set()
    return set(t) if isinstance(t, list) else {t}


def merge_schema(a, b):
    if a is None:
        return b
    if b is None:
        return a
    a_type, b_type = a.get("type"), b.get("type")
    types = _type_set(a_type) | _type_set(b_type)

    if types == {"object"}:
        return merge_object_schemas(a, b)
    if types == {"array"}:
        return merge_array_schemas(a, b)
    if types == {"string"}:
        if a.get("pattern") == b.get("pattern"):
            return a
        return {"type": "string"}
    if len(types) == 1:
        # same scalar type both sides (integer/number/boolean/null) -- nothing to merge
        return a if a == b else {"type": next(iter(types))}
    # genuinely different types observed for the same field across siblings
    # (e.g. a value that's sometimes a real value, sometimes null) -- union.
    return {"type": sorted(types)}


def merge_object_schemas(a, b):
    props = dict(a.get("properties", {}))
    for k, v in b.get("properties", {}).items():
        props[k] = merge_schema(props.get(k), v)
    required = sorted(set(a.get("required", [])) & set(b.get("required", [])))
    result = {"type": "object", "properties": props}
    if required:
        result["required"] = required
    result["additionalProperties"] = False
    return result


def merge_array_schemas(a, b):
    return {"type": "array", "items": merge_schema(a.get("items"), b.get("items"))}


# ============================================================================
# Manual overrides: enums, descriptions, and nullable-type fixes that
# structural inference alone can't know. Each entry is a path of YAML keys
# from the document root; array boundaries are handled automatically (a
# path segment always means "the property on the object here", stepping
# through an intervening array's `items` first if the current node is one).
# ============================================================================

def _descend(node, key):
    while node.get("type") == "array":
        node = node["items"]
    return node["properties"][key]


def apply_override(root, path, patch):
    node = root
    for key in path:
        node = _descend(node, key)
    node.update(patch)


LINK_TYPE_DESC = (
    "Link-speed/media class, keyed into this same document's "
    "link_standards mapping (its top-level keys are the closed set of "
    "valid values here)."
)

OVERRIDES = {
    "physical topology.yaml": [
        (["site_physical_topology", "wan_routers", "external_links", "type"],
         {"enum": ["wan_circuit"], "description": LINK_TYPE_DESC}),
        (["site_physical_topology", "wan_routers", "internal_links", "type"],
         {"enum": ["inter_device"], "description": LINK_TYPE_DESC}),
        (["site_physical_topology", "core_routers", "links", "type"],
         {"enum": ["inter_device", "core_to_agg"], "description": LINK_TYPE_DESC}),
        (["site_physical_topology", "aggregation_switches", "links", "type"],
         {"enum": ["inter_device"], "description": LINK_TYPE_DESC}),
        (["site_physical_topology", "floors", "access_switches", "uplinks", "type"],
         {"enum": ["agg_to_access"], "description": LINK_TYPE_DESC}),
        (["site_physical_topology", "floors"],
         {"description": "Only floor_number: 1 is spelled out; floors 2-10 "
                          "repeat this same access_switches pattern (see "
                          "design.md and the templates' own header notes)."}),
    ],
    "physical topology management network.yaml": [
        (["management_context", "management_tier", "mgt_wan_routers", "external_links", "type"],
         {"enum": ["mgt_wan_circuit"], "description": LINK_TYPE_DESC}),
        (["management_context", "management_tier", "mgt_wan_routers", "internal_links", "type"],
         {"enum": ["mgt_backbone"], "description": LINK_TYPE_DESC}),
        (["management_context", "management_tier", "mgt_core_switches", "links", "type"],
         {"enum": ["mgt_backbone"], "description": LINK_TYPE_DESC}),
        (["management_context", "management_tier", "mgt_access_nodes", "type"],
         {"enum": ["terminal_server", "mgt_switch"],
          "description": "What this MER-level OOB access node is: a console "
                          "terminal server (async_console_mappings) or a "
                          "management-plane switch (mgt_ethernet_mappings)."}),
        (["management_context", "management_tier", "mgt_access_nodes", "links", "type"],
         {"enum": ["mgt_backbone"], "description": LINK_TYPE_DESC}),
        (["management_context", "management_tier", "floors", "oob_nodes", "type"],
         {"enum": ["combo_console_switch"],
          "description": "Floor-level OOB node combining both console "
                          "(async_console_mappings) and switched-Ethernet "
                          "(mgt_ethernet_mappings) access in one device."}),
        (["management_context", "management_tier", "floors", "oob_nodes", "uplink", "type"],
         {"enum": ["mgt_backbone"], "description": LINK_TYPE_DESC}),
        (["management_context", "management_tier", "floors"],
         {"description": "Only floor_number: 1 is spelled out; floors 2-10 "
                          "repeat this same oob_nodes pattern, one per "
                          "production access switch pair (see physical "
                          "topology.yaml's own floors: for the pattern this "
                          "mirrors)."}),
    ],
    "logical topology.yaml": [
        (["site_context", "device_interconnects", "wan_routers", "routing", "loopbacks", "type"],
         {"enum": ["management"], "description": "What this loopback is used for."}),
        (["site_context", "device_interconnects", "wan_routers", "routing", "bgp_peers", "type"],
         {"enum": ["ebgp", "ibgp"], "description": "eBGP (to the ISP) or iBGP (underlay, within AS 65100)."}),
        (["site_context", "device_interconnects", "core_routers", "routing", "loopbacks", "type"],
         {"enum": ["management"], "description": "What this loopback is used for."}),
        (["site_context", "device_interconnects", "core_routers", "routing", "bgp_peers", "type"],
         {"enum": ["ibgp"], "description": "eBGP (to the ISP) or iBGP (underlay, within AS 65100)."}),
        (["site_context", "device_interconnects", "aggregation_switches", "role"],
         {"enum": ["aggregation-transit"], "description": "device_role() also derives this from the -agg- hostname convention; stated explicitly here too."}),
        (["site_context", "device_interconnects", "aggregation_switches", "routing", "loopbacks", "type"],
         {"enum": ["management"], "description": "What this loopback is used for."}),
        (["site_context", "device_interconnects", "aggregation_switches", "routing", "bgp_peers", "type"],
         {"enum": ["ibgp"], "description": "eBGP (to the ISP) or iBGP (underlay, within AS 65100)."}),
        (["site_context", "device_interconnects", "floors", "access_vteps", "role"],
         {"enum": ["access-vtep"], "description": "device_role() also derives this from the -acc- hostname convention; stated explicitly here too."}),
        (["site_context", "device_interconnects", "floors", "access_vteps", "evpn_vtep", "loopbacks", "type"],
         {"enum": ["management", "vtep-source"], "description": "management = Loopback0 (day-2 mgmt/underlay router-id source); vtep-source = Loopback1 (NVE/VXLAN tunnel source)."}),
        (["site_context", "device_interconnects", "floors", "access_vteps", "evpn_vtep", "bgp_peers", "type"],
         {"enum": ["ibgp"], "description": "eBGP (to the ISP) or iBGP (underlay, within AS 65100)."}),
        (["site_context", "device_interconnects", "floors"],
         {"description": "Only floor_number: 1 is spelled out; floors 2-10 "
                          "repeat this same access_vteps pattern."}),
        (["site_context", "evpn_overlay_design", "vni_service_mappings"],
         {"description": "The single source of truth for VNI/VLAN service "
                          "mappings -- endpoint service.yaml's per-port "
                          "config references vlan_id values from here "
                          "rather than redefining them. Only VNI 10 "
                          "(Campus_Users) carries anycast_gateway_ip / "
                          "vrf_name / route_distinguisher / route_targets / "
                          "dhcp_server -- VNIs 20/30/40/50/999 are a known, "
                          "documented data-model gap, not omitted here."}),
    ],
    "wan edge role.yaml": [
        (["platform_wan_baseline", "management_plane", "syslog", "source_interface"],
         {"type": ["string", "null"], "description": "null = no syslog servers configured, so nothing to source from."}),
        (["platform_wan_baseline", "management_plane", "syslog", "severity_level"],
         {"type": ["string", "null"], "description": "null = no syslog servers configured, so no severity level set."}),
        (["platform_wan_baseline", "management_plane", "tacacs", "source_interface"],
         {"type": ["string", "null"], "description": "null = no TACACS+ servers configured, so nothing to source from."}),
        (["platform_wan_baseline", "management_plane", "tacacs", "encryption_key"],
         {"type": ["string", "null"], "description": "null = no TACACS+ servers configured, so no shared key."}),
        (["platform_wan_baseline", "management_plane", "syslog", "servers"],
         {"items": {"type": "string"}, "description": "Empty in this data model -- documented gap (no syslog servers configured), not a fabricated default. Items are hostname/IP strings, same shape as ntp.servers."}),
        (["platform_wan_baseline", "management_plane", "tacacs", "servers"],
         {"items": {"type": "string"}, "description": "Empty in this data model -- documented gap (no TACACS+ servers configured), not a fabricated default. Items are hostname/IP strings, same shape as ntp.servers."}),
        (["platform_wan_baseline", "routing_baseline", "control_plane_policing", "protocols", "routing_updates"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
        (["platform_wan_baseline", "routing_baseline", "control_plane_policing", "protocols", "management_access"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
        (["platform_wan_baseline", "routing_baseline", "control_plane_policing", "protocols", "transit_traffic"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
    ],
    "core agg role.yaml": [
        (["platform_core_agg_baseline", "management_plane", "syslog", "source_interface"],
         {"type": ["string", "null"], "description": "null = no syslog servers configured, so nothing to source from."}),
        (["platform_core_agg_baseline", "management_plane", "syslog", "severity_level"],
         {"type": ["string", "null"], "description": "null = no syslog servers configured, so no severity level set."}),
        (["platform_core_agg_baseline", "management_plane", "tacacs", "source_interface"],
         {"type": ["string", "null"], "description": "null = no TACACS+ servers configured, so nothing to source from."}),
        (["platform_core_agg_baseline", "management_plane", "tacacs", "encryption_key"],
         {"type": ["string", "null"], "description": "null = no TACACS+ servers configured, so no shared key."}),
        (["platform_core_agg_baseline", "management_plane", "syslog", "servers"],
         {"items": {"type": "string"}, "description": "Empty in this data model -- documented gap (no syslog servers configured), not a fabricated default. Items are hostname/IP strings, same shape as ntp.servers."}),
        (["platform_core_agg_baseline", "management_plane", "tacacs", "servers"],
         {"items": {"type": "string"}, "description": "Empty in this data model -- documented gap (no TACACS+ servers configured), not a fabricated default. Items are hostname/IP strings, same shape as ntp.servers."}),
        (["platform_core_agg_baseline", "routing_baseline", "control_plane_policing", "protocols", "routing_updates"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
        (["platform_core_agg_baseline", "routing_baseline", "control_plane_policing", "protocols", "management_access"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
        (["platform_core_agg_baseline", "routing_baseline", "control_plane_policing", "protocols", "transit_traffic"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
    ],
    "access role.yaml": [
        (["platform_access_baseline", "management_plane", "syslog", "source_interface"],
         {"type": ["string", "null"], "description": "null = no syslog servers configured, so nothing to source from."}),
        (["platform_access_baseline", "management_plane", "syslog", "severity_level"],
         {"type": ["string", "null"], "description": "null = no syslog servers configured, so no severity level set."}),
        (["platform_access_baseline", "management_plane", "tacacs", "source_interface"],
         {"type": ["string", "null"], "description": "null = no TACACS+ servers configured, so nothing to source from."}),
        (["platform_access_baseline", "management_plane", "tacacs", "encryption_key"],
         {"type": ["string", "null"], "description": "null = no TACACS+ servers configured, so no shared key."}),
        (["platform_access_baseline", "management_plane", "syslog", "servers"],
         {"items": {"type": "string"}, "description": "Empty in this data model -- documented gap (no syslog servers configured), not a fabricated default. Items are hostname/IP strings, same shape as ntp.servers."}),
        (["platform_access_baseline", "management_plane", "tacacs", "servers"],
         {"items": {"type": "string"}, "description": "Empty in this data model -- documented gap (no TACACS+ servers configured), not a fabricated default. Items are hostname/IP strings, same shape as ntp.servers."}),
        (["platform_access_baseline", "routing_baseline", "control_plane_policing", "protocols", "routing_updates"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
        (["platform_access_baseline", "routing_baseline", "control_plane_policing", "protocols", "management_access"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
        (["platform_access_baseline", "routing_baseline", "control_plane_policing", "protocols", "transit_traffic"],
         {"enum": ["low", "medium", "high"], "description": "CoPP priority tier (rate is derived from this in the template, not stored here)."}),
    ],
    "endpoint service.yaml": [
        (["site_context", "endpoint_interfaces", "port_overrides", "voice_vlan"],
         {"type": ["integer", "null"], "description": "null = voice disabled on this override (e.g. a camera port)."}),
        (["site_context", "endpoint_interfaces", "port_overrides", "switch"],
         {"type": ["string", "null"], "description": "null/absent = this override applies to every access switch; a hostname string scopes it to just that one switch. Both existing entries are currently null (site-wide); a real hostname value is written here by scripts/set_endpoint_port.py / playbooks/bau_endpoint_provisioning.yml when someone records a switch-specific BAU change."}),
    ],
    "telemetry.yaml": [
        (["site_telemetry", "telemetry_destinations", "protocol"],
         {"enum": ["grpc"], "description": "Transport protocol devices use to reach the collector."}),
        (["site_telemetry", "telemetry_destinations", "encoding"],
         {"enum": ["gpb-kv", "gpb-compact", "json"], "description": "Wire encoding for the streamed data -- gpb-kv is self-describing (no compiled .proto needed at the collector); gpb-compact is smaller but needs matching .proto definitions; json trades size for human readability."}),
        (["site_telemetry", "telemetry_destinations", "transport"],
         {"enum": ["dial-out"], "description": "dial-out = device pushes to the collector; no inbound reachability to devices required. dial-in (collector pulls via gNMI) is not modelled here."}),
        (["site_telemetry", "role_subscriptions"],
         {"description": "Keyed by device_role() value (wan-edge / core / aggregation-transit / access-vtep). A role with no entry here is a documented gap -- device_telemetry_subscription() returns an empty subscription for it rather than guessing."}),
    ],
}

# ============================================================================
# Per-file metadata (title/description drawn from design.md's own Data
# Models / Device Role Models tables) + output filename
# ============================================================================

MODEL_FILES = [
    ("physical topology.yaml", "physical-topology",
     "Physical Topology - Campus Network",
     "Ground-truth inventory of campus network hardware and cabling -- "
     "devices, ports, and interconnects."),
    ("physical topology management network.yaml", "physical-topology-management-network",
     "Physical Topology - Management Network",
     "Ground-truth inventory of the OOB management network -- terminal "
     "servers, management switches, and console cabling."),
    ("logical topology.yaml", "logical-topology",
     "Logical Topology",
     "The campus's BGP underlay and VXLAN EVPN overlay -- how traffic is "
     "forwarded and isolated, independent of physical hardware."),
    ("endpoint service.yaml", "endpoint-service",
     "Endpoint Service",
     "Standardized security and QoS baseline for endpoint switchports -- "
     "loop protection, 802.1X/MAB, FHS, and edge QoS."),
    ("wan edge role.yaml", "wan-edge-role",
     "WAN Edge Role (platform: Catalyst 8000)",
     "Platform-agnostic hardening/security/operational baseline for WAN "
     "edge routers, rendered by templates/catalyst 8000.j2."),
    ("core agg role.yaml", "core-agg-role",
     "Core & Aggregation Role (platform: Nexus 93240)",
     "Platform-agnostic hardening/security/operational baseline for core "
     "and aggregation switches, rendered by templates/nexus 93240.j2."),
    ("access role.yaml", "access-role",
     "Access Role (platform: Catalyst 9000)",
     "Platform-agnostic hardening/security/operational baseline for "
     "access switches, rendered by templates/catalyst 9000.j2."),
    ("telemetry.yaml", "telemetry",
     "Streaming Telemetry",
     "Model-driven telemetry (MDT) subscriptions -- destinations and "
     "sensor groups, assigned per device role -- rendered by "
     "templates/telemetry.j2."),
]


def build_schema(repo_root, filename, slug, title, description):
    with open(os.path.join(repo_root, "models", filename)) as f:
        data = yaml.safe_load(f)

    schema = infer_object_schema(data)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_ID_BASE}/{slug}.schema.json",
        "title": title,
        "description": (
            f"{description} Structurally inferred from "
            f"models/{filename} by scripts/generate_schemas.py -- "
            "regenerate after any change to that file rather than "
            "hand-editing this one."
        ),
        **schema,
    }

    for path, patch in OVERRIDES.get(filename, []):
        apply_override(schema, path, patch)

    return schema


def main():
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    out_dir = os.path.join(repo_root, "schemas")
    os.makedirs(out_dir, exist_ok=True)

    for filename, slug, title, description in MODEL_FILES:
        schema = build_schema(repo_root, filename, slug, title, description)
        out_path = os.path.join(out_dir, f"{slug}.schema.json")
        with open(out_path, "w") as f:
            json.dump(schema, f, indent=2)
            f.write("\n")
        print(f"wrote {out_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
