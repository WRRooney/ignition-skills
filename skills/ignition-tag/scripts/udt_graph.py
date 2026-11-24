#!/usr/bin/env python3
"""Read-only UDT dependency graph from a tag export.

A type depends on its parent (`typeId` on the type) and on every type it embeds
(`typeId` on a UdtInstance member). Writes must go dependencies first ("root down").

  python3 udt_graph.py EXPORT.json impact TYPE [TYPE ...]
      Types and instances affected by editing TYPE, plus the root-down write order.
  python3 udt_graph.py EXPORT.json order [--new FOLDER:FILE ...] TYPE [TYPE ...]
      Root-down write order for the given types; --new adds type JSON files not yet
      written (FOLDER is the `ign tag udt-type --path`). Exit 1 on a missing dependency.
  python3 udt_graph.py EXPORT.json collide TYPE MEMBER [MEMBER ...]
      Before adding MEMBER (path inside the type, e.g. Status/Fault) to TYPE: descendant
      types that already declare it, and instances overriding it. The gateway renames the
      descendant's copy to <name>_duplicate_N. Exit 1 if any.
  python3 udt_graph.py EXPORT.json duplicates
      Every type member, instance member, and tag named *_duplicate_N. Exit 1 if any.

EXPORT.json: ign api GET '/data/api/v1/tags/export?provider=P&recursive=true&includeUdts=true&type=json' --out EXPORT.json
"""
from __future__ import annotations

import json
import re
import sys

DUP = re.compile(r"_duplicate_\d+$")


def _member_deps(node: dict) -> set[str]:
    deps = set()
    for m in node.get("tags") or []:
        if m.get("tagType") == "UdtInstance" and m.get("typeId"):
            deps.add(m["typeId"])
        deps |= _member_deps(m)
    return deps


def _deps(t: dict) -> set[str]:
    return ({t["typeId"]} if t.get("typeId") else set()) | _member_deps(t)


NODES: dict[str, dict] = {}  # type path -> type node
INSTANCES: dict[str, dict] = {}  # instance path -> instance node


def load(path: str) -> tuple[dict[str, set[str]], list[tuple[str, str]]]:
    """Return ({type path: dependency type paths}, [(instance path, typeId)])."""
    root = json.load(open(path, encoding="utf-8"))
    types: dict[str, set[str]] = {}
    instances: list[tuple[str, str]] = []

    def walk_types(n: dict, prefix: str) -> None:
        for c in n.get("tags") or []:
            p = f"{prefix}{c['name']}"
            if c.get("tagType") == "UdtType":
                types[p] = _deps(c)
                NODES[p] = c
            elif c.get("tagType") == "Folder":
                walk_types(c, p + "/")

    def walk_tags(n: dict, prefix: str) -> None:
        for c in n.get("tags") or []:
            p = f"{prefix}{c['name']}"
            if c.get("tagType") == "UdtInstance" and c.get("typeId"):
                instances.append((p, c["typeId"]))  # members come with their owner
                INSTANCES[p] = c
            elif c.get("tagType") == "Folder":
                walk_tags(c, p + "/")

    for top in root.get("tags") or []:
        if top.get("name") == "_types_":
            walk_types(top, "")
        else:
            walk_tags({"tags": [top]}, "")
    return types, instances


def root_down(selected: set[str], graph: dict[str, set[str]]) -> list[str]:
    """Order `selected` so every type follows the selected types it depends on."""
    out: list[str] = []
    seen: set[str] = set()

    def visit(t: str, stack: tuple[str, ...]) -> None:
        if t in seen:
            return
        if t in stack:
            raise SystemExit(f"cycle: {' -> '.join(stack + (t,))}")
        for d in sorted(graph.get(t, ())):
            if d in selected:
                visit(d, stack + (t,))
        seen.add(t)
        out.append(t)

    for t in sorted(selected):
        visit(t, ())
    return out


def impact(graph: dict[str, set[str]], instances: list[tuple[str, str]], targets: list[str]) -> int:
    missing = [t for t in targets if t not in graph]
    if missing:
        print(f"unknown type(s): {', '.join(missing)}", file=sys.stderr)
        return 1
    affected = set(targets)
    changed = True
    while changed:  # dependents: children by typeId and types embedding an affected type
        changed = False
        for t, deps in graph.items():
            if t not in affected and deps & affected:
                affected.add(t)
                changed = True
    hits = sorted(p for p, tid in instances if tid in affected)
    print("Write order (root down):")
    for t in root_down(affected, graph):
        why = "edited" if t in targets else "depends on " + ", ".join(sorted(graph[t] & affected))
        print(f"  {t}  ({why})")
    print(f"Affected instances: {len(hits)}")
    for p in hits:
        print(f"  {p}")
    return 0


def order(graph: dict[str, set[str]], args: list[str]) -> int:
    selected: list[str] = []
    while args:
        a = args.pop(0)
        if a == "--new":
            folder, _, file = args.pop(0).partition(":")
            data = json.load(open(file, encoding="utf-8"))
            for t in data if isinstance(data, list) else [data]:
                p = f"{folder.strip('/')}/{t['name']}" if folder.strip("/") else t["name"]
                graph[p] = _deps(t)
                selected.append(p)
        else:
            selected.append(a)
    bad = [(t, d) for t in selected for d in sorted(graph.get(t, ())) if d not in graph]
    for t, d in bad:
        print(f"missing dependency: {t} needs {d}, which is neither on the gateway nor in this change", file=sys.stderr)
    if bad:
        return 1
    print("Write order (root down):")
    for t in root_down(set(selected), graph):
        print(f"  {t}")
    return 0


def _member_paths(node: dict, prefix: str = "") -> dict[str, str]:
    """Declared member paths of a type or instance node, keyed lowercase (tag paths are case-insensitive)."""
    out: dict[str, str] = {}
    for m in node.get("tags") or []:
        p = f"{prefix}{m['name']}"
        out[p.lower()] = p
        out.update(_member_paths(m, p + "/"))
    return out


def collide(graph: dict[str, set[str]], instances: list[tuple[str, str]], args: list[str]) -> int:
    target, members = args[0], [m.strip("/").lower() for m in args[1:]]
    if target not in graph:
        print(f"unknown type: {target}", file=sys.stderr)
        return 1
    desc = {target}
    changed = True
    while changed:  # inheritance only: embedding does not merge members
        changed = False
        for t in graph:
            if t not in desc and NODES[t].get("typeId") in desc:
                desc.add(t)
                changed = True
    hits = []
    for t in sorted(desc - {target}):
        own = _member_paths(NODES[t])
        hits += [f"type {t}: declares {own[m]}" for m in members if m in own]
    for p, tid in sorted(instances):
        if tid in desc:
            own = _member_paths(INSTANCES[p])
            hits += [f"instance {p} ({tid}): overrides {own[m]}" for m in members if m in own]
    for h in hits:
        print(h)
    print(f"{len(hits)} collision(s)")
    return 1 if hits else 0


def duplicates(path: str) -> int:
    hits = []

    def walk(n: dict, prefix: str, in_types: bool, in_instance: bool) -> None:
        for c in n.get("tags") or []:
            p = f"{prefix}{c['name']}"
            if DUP.search(c["name"]):
                kind = "type member" if in_types else "instance member" if in_instance else "tag"
                hits.append(f"{kind} {p}")
            walk(c, p + "/", in_types, in_instance or c.get("tagType") == "UdtInstance")

    for top in json.load(open(path, encoding="utf-8")).get("tags") or []:
        if top.get("name") == "_types_":
            walk(top, "", True, False)  # type paths without the synthetic _types_ prefix
        else:
            walk({"tags": [top]}, "", False, False)
    for h in hits:
        print(h)
    print(f"{len(hits)} duplicate(s)")
    return 1 if hits else 0


def main(argv: list[str]) -> int:
    cmds = ("impact", "order", "collide", "duplicates")
    if len(argv) < 2 or argv[1] not in cmds or (argv[1] != "duplicates" and len(argv) < 3) \
            or (argv[1] == "collide" and len(argv) < 4):
        print(__doc__, file=sys.stderr)
        return 2
    if argv[1] == "duplicates":
        return duplicates(argv[0])
    graph, instances = load(argv[0])
    if argv[1] == "collide":
        return collide(graph, instances, argv[2:])
    return impact(graph, instances, argv[2:]) if argv[1] == "impact" else order(graph, argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
