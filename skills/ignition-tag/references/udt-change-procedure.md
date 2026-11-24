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

When a child type already declares a member and the same member is added to its parent,
what happens depends on how the parent is written (verified on a live gateway, November 2026):

| Parent written with | Result on the child | Instance overrides of that member |
|---|---|---|
| `ign tag udt-type` or a `set-udt-*` verb (disk write + config scan) | No rename. The child's member becomes an override of the inherited one and keeps its own settings | Kept |
| `/tags/import` with a `_types_` body (`ign tag import`, a Designer JSON import) | Renamed to `<name>_duplicate_1` (then `_2`, ...) next to the inherited member. The child's file on disk still shows the old name, so the gateway and disk disagree | Moved onto the instance's `_duplicate_N` member |
| `/tags/import` with parent and child together, or the child stripped first | No rename | Lost |

So write type changes only with `ign tag udt-type` and the `set-udt-*` patch verbs, never
by importing a `_types_` body. Check for collisions before the write anyway:

```bash
python3 <skill-dir>/scripts/udt_graph.py .ign/tags-default.json collide Equipment/Motor Status/Fault Speed
```

Member paths are relative to the type and matched case-insensitively. The output lists each
descendant type that declares the member and each instance that overrides it; exit 1 means
collisions. Each listed child keeps its own definition as an override, so its settings win
over the parent's new ones. Include the collisions in the approval request and ask whether
each child's settings should stay as overrides or be removed so the parent's definition
applies. Removing them is a separate child edit, written after the parent lands.

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

Duplicates come from a parent gaining a member a child already had through `/tags/import`,
or from an import that collided with existing tags (`tag-import.md`). Cleanup is an edit
like any other: run `impact` on each child type that holds one, and get the user's approval
first. Show which instances carry values on the duplicate, because cleanup drops them.

Verified on a live gateway for a duplicate created by an import:

- Rewriting the child unchanged with `ign tag udt-type` does nothing; the duplicate stays.
- Rewriting the child with the member removed, or reduced to an override that keeps only
  the keys that differ from the parent (`udt-member-inheritance.md`), clears the duplicate
  from the child and from its instances.
- Instance values that had moved onto the duplicate are lost in that step.

Procedure:

1. Record the instances' values and overrides on the duplicate (from the export).
2. Rewrite each affected child type, root down, with `ign tag udt-type`: drop the member if
   the parent's definition should apply, or keep only the differing keys as an override.
3. Re-apply the recorded instance overrides on the real member name (`ign tag import` of the
   instances, `udt-instances.md`; overrides must restate `valueSource`,
   `udt-instance-overrides.md`).
4. Re-export and run `duplicates` again; it should report 0.
