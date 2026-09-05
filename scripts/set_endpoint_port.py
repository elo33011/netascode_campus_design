#!/usr/bin/env python3
"""
Record one real BAU switchport change directly in
models/endpoint service.yaml -- adds or updates a `switch`-scoped
endpoint_interfaces.port_overrides entry for one access switch + one
interface, so the change becomes part of the persisted data model (the
next render/validate/push, by anyone, for any reason, reflects it) rather
than a one-off runtime CLI override that the next full re-push would
silently revert.

Deliberately does NOT parse-then-re-dump the whole YAML file (which would
strip every one of its inline comments -- this repo's data models rely on
those comments throughout). Instead it does a precise, anchored text
edit -- find-exactly-one-then-replace, or a clean append -- the same
discipline every other scripts/patch_*.py in this repo already follows,
just parameterised for repeated/scripted use (this one is meant to be run
by playbooks/bau_endpoint_provisioning.yml, not just once by hand).

The result is re-parsed with yaml.safe_load() before being written back
to disk, as a safety net against any edge case in the text surgery
producing invalid YAML -- if that check fails, nothing is written.

Usage:
  set_endpoint_port.py <repo_root> --switch <hostname> --interface <ifname>
      --vlan <n> [--voice-vlan <n|none>] [--description <text>]

Example:
  set_endpoint_port.py . --switch abc-hq-f01-acc-01 \\
      --interface GigabitEthernet1/0/5 --vlan 20 --voice-vlan 30 \\
      --description "Marketing desk move, INC0012345"
"""
import argparse
import os
import re
import sys

import yaml

ENTRY_START_RE = re.compile(r'^ {6}- interface: "([^"]+)"\s*$')
SWITCH_LINE_RE = re.compile(r'^ {8}switch: (.+)\s*$')


def parse_yaml_scalar(raw):
    """'"abc-hq-f01-acc-01"' -> 'abc-hq-f01-acc-01', 'null' -> None."""
    raw = raw.strip()
    if raw == 'null' or raw == '~':
        return None
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    return raw


def find_entries(lines, start_idx):
    """From the line right after 'port_overrides:', return a list of
    (interface, switch, start_line_idx, end_line_idx_exclusive) for every
    existing port_overrides entry. An entry runs from its '- interface:'
    line through the last line more deeply indented than that marker
    (6 spaces + '- '), i.e. up to (not including) the next '      - '
    line or a line indented <=6 spaces, or EOF."""
    entries = []
    i = start_idx
    n = len(lines)
    while i < n:
        m = ENTRY_START_RE.match(lines[i])
        if not m:
            break
        iface = m.group(1)
        entry_start = i
        switch = None
        j = i + 1
        while j < n:
            line = lines[j]
            if ENTRY_START_RE.match(line):
                break
            if line.strip() == '' :
                j += 1
                continue
            indent = len(line) - len(line.lstrip(' '))
            if indent <= 6:
                break
            sm = SWITCH_LINE_RE.match(line)
            if sm:
                switch = parse_yaml_scalar(sm.group(1))
            j += 1
        entries.append((iface, switch, entry_start, j))
        i = j
    return entries


def build_entry_lines(interface, switch, vlan, voice_vlan, description):
    lines = [f'      - interface: "{interface}"']
    lines.append(f'        switch: "{switch}"')
    if description is not None:
        esc = description.replace('"', '\\"')
        lines.append(f'        description: "{esc}"')
    lines.append(f'        access_vlan: {vlan}')
    if voice_vlan is not None:
        if isinstance(voice_vlan, str) and voice_vlan.lower() == 'none':
            lines.append('        voice_vlan: null')
        else:
            lines.append(f'        voice_vlan: {int(voice_vlan)}')
    return [l + '\n' for l in lines]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('repo_root')
    ap.add_argument('--switch', required=True, help='access switch hostname, e.g. abc-hq-f01-acc-01')
    ap.add_argument('--interface', required=True, help='interface name, e.g. GigabitEthernet1/0/5')
    ap.add_argument('--vlan', required=True, type=int, help='intended access VLAN')
    ap.add_argument('--voice-vlan', default=None, help='intended voice VLAN, or "none" to explicitly clear it')
    ap.add_argument('--description', default=None)
    args = ap.parse_args()

    path = os.path.join(args.repo_root, 'models', 'endpoint service.yaml')
    with open(path) as f:
        original = f.read()
    lines = original.splitlines(keepends=True)

    anchor_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == 'port_overrides:':
            anchor_idx = idx
            break
    if anchor_idx is None:
        print(f"ERROR: 'port_overrides:' anchor not found in {path}", file=sys.stderr)
        return 1

    entries = find_entries(lines, anchor_idx + 1)
    new_entry_lines = build_entry_lines(args.interface, args.switch, args.vlan, args.voice_vlan, args.description)

    match = None
    for iface, switch, start, end in entries:
        if iface == args.interface and switch == args.switch:
            match = (start, end)
            break

    if match:
        start, end = match
        action = f"updated existing switch-scoped override for {args.switch} {args.interface}"
        lines = lines[:start] + new_entry_lines + lines[end:]
    else:
        insert_at = entries[-1][3] if entries else anchor_idx + 1
        action = f"added new switch-scoped override for {args.switch} {args.interface}"
        lines = lines[:insert_at] + new_entry_lines + lines[insert_at:]

    new_content = ''.join(lines)

    # Safety net: never write back anything that doesn't parse.
    try:
        yaml.safe_load(new_content)
    except yaml.YAMLError as e:
        print(f"ERROR: edit would produce invalid YAML, nothing written: {e}", file=sys.stderr)
        return 1

    with open(path, 'w') as f:
        f.write(new_content)

    print(f"OK: {action} in {path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
