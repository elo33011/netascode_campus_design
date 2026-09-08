#!/usr/bin/env python3
"""
Renders the full per-device configuration for every device in
physical_topology.yaml by chaining, in the order design.md's "Step 1.
Baseline Build" workflow specifies:
  1. the platform baseline template (catalyst 8000.j2 / nexus 93240.j2 /
     catalyst 9000.j2)  -- device-wide hardening, no topology data
  2. physical topology.j2  -- hostname, interfaces up + described
  3. logical topology.j2   -- loopbacks, IP addressing, BGP, EVPN overlay
  4. telemetry.j2          -- every device; streaming telemetry (MDT)
     subscription from telemetry.yaml, resolved per device by role -- the
     "read path" back from devices, closing the loop stages 1-3 (the
     "write path") open
  5. endpoint service.j2   -- access-vtep devices only; BAU switchport
     provisioning from endpoint service.yaml, chained here purely so the
     one rendered_configs/<hostname>.cfg per device stays the complete,
     current picture -- playbooks/bau_endpoint_provisioning.yml is the
     one that actually re-runs this stage on its own for a real BAU change,
     independent of stages 1-4.

Usage: render_configs.py <repo_root> <output_dir>
"""
import sys
import os
import yaml
import jinja2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'filter_plugins'))
from netascode_filters import FILTERS, device_platform, device_role


PLATFORM_MAP = {
    'catalyst8000': {
        'baseline_template': 'catalyst 8000.j2',
        'baseline_yaml': 'wan edge role.yaml',
        'baseline_var': 'platform_wan_baseline',
    },
    'nexus93240': {
        'baseline_template': 'nexus 93240.j2',
        'baseline_yaml': 'core agg role.yaml',
        'baseline_var': 'platform_core_agg_baseline',
    },
    'catalyst9000': {
        'baseline_template': 'catalyst 9000.j2',
        'baseline_yaml': 'access role.yaml',
        'baseline_var': 'platform_access_baseline',
    },
}


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


def main():
    repo_root, out_dir = sys.argv[1], sys.argv[2]
    models_dir = os.path.join(repo_root, 'models')
    templates_dir = os.path.join(repo_root, 'templates')
    os.makedirs(out_dir, exist_ok=True)

    phys = load_yaml(os.path.join(models_dir, 'physical topology.yaml'))['site_physical_topology']
    logical = load_yaml(os.path.join(models_dir, 'logical topology.yaml'))['site_context']
    endpoint_service = load_yaml(os.path.join(models_dir, 'endpoint service.yaml'))['site_context']
    telemetry = load_yaml(os.path.join(models_dir, 'telemetry.yaml'))['site_telemetry']

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([templates_dir]),
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
    )
    env.filters.update(FILTERS)

    phys_tpl = env.get_template('physical topology.j2')
    log_tpl = env.get_template('logical topology.j2')
    endpoint_tpl = env.get_template('endpoint service.j2')
    telemetry_tpl = env.get_template('telemetry.j2')

    findings = []

    for name in all_device_names(phys):
        platform = device_platform(name)
        role = device_role(name)
        pm = PLATFORM_MAP[platform]

        baseline_data = load_yaml(os.path.join(models_dir, pm['baseline_yaml']))[pm['baseline_var']]
        baseline_tpl = env.get_template(pm['baseline_template'])
        baseline_ctx = {pm['baseline_var']: baseline_data}
        baseline_out = baseline_tpl.render(**baseline_ctx)

        phys_out = phys_tpl.render(
            site_physical_topology=phys,
            device_name=name,
            platform=platform,
        )

        log_out = log_tpl.render(
            site_physical_topology=phys,
            site_context=logical,
            device_name=name,
            platform=platform,
            role=role,
            platform_baseline=baseline_data,
        )

        telemetry_out = telemetry_tpl.render(
            site_telemetry=telemetry,
            device_name=name,
            platform=platform,
        )

        stage_5_header = ""
        stage_5_out = ""
        if role == 'access-vtep':
            endpoint_out = endpoint_tpl.render(
                platform_access_baseline=baseline_data,
                endpoint_service=endpoint_service,
                device_name=name,
                platform=platform,
            )
            stage_5_header = "! ---------- 5. Endpoint service (endpoint service.j2, BAU) ----------\n"
            stage_5_out = f"{endpoint_out}\n"

        full = (
            f"! ============================================================\n"
            f"! {name}  (platform: {platform}, role: {role})\n"
            f"! Rendered: baseline -> physical topology -> logical topology -> telemetry"
            f"{' -> endpoint service' if role == 'access-vtep' else ''}\n"
            f"! ============================================================\n\n"
            f"! ---------- 1. Platform baseline ({pm['baseline_template']} + {pm['baseline_yaml']}) ----------\n"
            f"{baseline_out}\n"
            f"! ---------- 2. Physical topology (physical topology.j2) ----------\n"
            f"{phys_out}\n"
            f"! ---------- 3. Logical topology (logical topology.j2) ----------\n"
            f"{log_out}\n"
            f"! ---------- 4. Streaming telemetry (telemetry.j2) ----------\n"
            f"{telemetry_out}\n"
            f"{stage_5_header}{stage_5_out}"
        )

        out_path = os.path.join(out_dir, f"{name}.cfg")
        with open(out_path, 'w') as f:
            f.write(full)
        print(f"wrote {out_path} ({len(full)} bytes)")

    print("\nDone.")


if __name__ == '__main__':
    main()
