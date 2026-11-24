# Changing UDT definitions: order and impact

UDT types form a dependency graph. A type depends on:

- its **parent** (`typeId` on the type: `Physics/GameObject` inherits `VCGEngine/Entity`), and
- every type it **embeds** (`typeId` on a `UdtInstance` member: `Entity` embeds `Vector2D`).

A type written before its dependencies exist, or before a changed dependency has landed,
loads against the wrong shape: members go missing, inherited overrides attach to nothing,
and instances export as `tagType: Unknown` with no error from `ign`. So every change runs
**root down**: dependencies first, then each type that depends on them.

## 1. Export the provider

```bash
ign api GET '/data/api/v1/tags/export?provider=default&recursive=true&includeUdts=true&type=json' --out .ign/tags-default.json
```

`type=json` is required; without it the gateway answers 400. This is read-only.

## 2. Adding types: get the write order

`scripts/udt_graph.py` lives in this skill's directory (next to `SKILL.md`). It reads the export
and never writes anything.

```bash
python3 <skill-dir>/scripts/udt_graph.py .ign/tags-default.json order --new Equipment:motor.json --new Equipment/Pumps:pump.json
```

`--new FOLDER:FILE` names each type file you are about to write, with `FOLDER` being its
`ign tag udt-type --path`. The script prints the root-down order, or exits 1 with
`missing dependency: X needs Y`. A missing dependency means a parent or embedded type is
neither on the gateway nor in this change. Stop and ask the user; do not invent the parent.

New types that nothing on the gateway depends on yet need no approval beyond the user's
request, but the order still applies.

## 3. Editing existing types: impact check, then approval

Before changing any existing type (member added or removed, member kind, data type,
parameters, alarms, `typeId`, rename), run:

```bash
python3 <skill-dir>/scripts/udt_graph.py .ign/tags-default.json impact Equipment/Motor
```

It lists every affected type in root-down order: the edited type, its descendants through
`typeId`, and every type that embeds an affected type. It also lists every instance whose
`typeId` is an affected type, because each of those instances changes when the type does.

### Adding a member to a type with descendants

Write type changes only with `ign tag udt-type` and the `set-udt-*` verbs, never by importing
a `_types_` body. An import renames a child's same-named member to `<name>_duplicate_N` and
moves instance overrides onto the duplicate; `udt-type` turns the child's member into an
override of the inherited one instead.

Check for collisions before the write:

```bash
python3 <skill-dir>/scripts/udt_graph.py .ign/tags-default.json collide Equipment/Motor Status/Fault Speed
```

Member paths are relative to the type and matched case-insensitively; exit 1 means
collisions. Each listed child type keeps its own definition as an override, so its settings
win over the parent's. In the approval request, ask whether each child's settings stay as
overrides or are removed so the parent's definition applies. Removing them is a separate
child edit, written after the parent lands.

Then **stop and ask the user for approval**, showing:

1. The change, per type, as the `--dry-run` payloads.
2. The write order from `impact` (or `order`).
3. The affected instance count and paths. Show all of them if there are 20 or fewer;
   otherwise show the count per folder.
4. Known risks:
   - an instance override of a changed member may now point at nothing (`udt-instance-overrides.md`);
   - a member kind change is refused by the scan (`udt-scan-merge-semantics.md`);
   - a removed member drops its value and history.

Write nothing until the user approves. A new user request that changes the plan needs a
new impact check and new approval.

## 4. Write root down, verifying each level

For each type in the order:

1. `ign tag udt-type ... --dry-run` (or a `set-udt-*` patch verb with `--dry-run`).
2. Run the real write. It scans config automatically.
3. Re-export (step 1) and confirm the type under `_types_/` shows the change before
   writing the next type. If a `WARNING:` scan line appears or the type is missing,
   stop and report; do not continue down the tree.

Types in the same folder share one `udts.json`, so one write covers them all. If one
folder holds both a changed type and a type that depends on something in a folder written
later, stop and tell the user the order cannot be satisfied with whole-folder writes.

## 5. After the last type

Re-run `impact` against a fresh export and spot-check a few listed instances in the
export (`tagType` is `UdtInstance`, not `Unknown`, and members are present). Then check for
renamed collisions:

```bash
python3 <skill-dir>/scripts/udt_graph.py .ign/tags-default.json duplicates
```

It lists every type member, instance member, and tag whose name ends in `_duplicate_N`
(exit 1 if any). Report what changed, which instances were affected, and any duplicates.

## Cleaning up `_duplicate_N` members

Cleanup is an edit: run `impact` on each child type that holds a duplicate and get the
user's approval first. Instance values on the duplicate are dropped by step 2, so list them
in the request.

1. Record the instances' values and overrides on the duplicate (from the export).
2. Rewrite each affected child type, root down, with `ign tag udt-type`: drop the member if
   the parent's definition should apply, or keep only the keys that differ as an override
   (`udt-member-inheritance.md`). Rewriting the child unchanged does not clear a duplicate.
3. Re-apply the recorded instance overrides on the real member name (`ign tag import` of the
   instances, `udt-instances.md`; overrides must restate `valueSource`,
   `udt-instance-overrides.md`).
4. Re-export and run `duplicates`; it should report 0.
