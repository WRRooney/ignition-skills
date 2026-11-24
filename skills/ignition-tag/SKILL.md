---
name: ignition-tag
description: |
  Use when the user wants to author, preview, push, import, patch or delete Ignition tags with the `ign tag` verbs: memory/OPC/expression tags, alarms on tags, UDT type definitions, UDT instances, member property patches, tag value writes, and the verification steps around them.
  Positive triggers: "push tag", "build tag", "memory tag", "OPC tag at", "tag at default", "preview tag JSON", "Tanks/T01", "dataType Float8", "UDT", "udt-type", "udt-instance", "UDT instance override", "set a tag value", "tags/import", "alarm on a tag", "Alarm Metrics", "delete tag".
  Do not trigger for: git tag, html tag, image alt tag, Docker image tags, tag providers themselves (use ignition-provider), Perspective tag bindings inside a view (use ignition-perspective).
---

# Tags with `ign tag`

## Rules

1. Only `ign tag` verbs write tag and UDT files; never hand-edit `tags.json`, `udts.json`, or
   `unary-resource.json`. If a shape is not expressible, stop and tell the user what is missing.
2. `--dry-run` first on anything that writes. Use only options `--help` lists.
3. Surface `ign`'s stdout and any `Error:` / `Hint:` lines verbatim.
4. Writes scan automatically; do not add a scan. `--no-scan` only when the gateway is unreachable.
5. Confirm the path with the user before any delete without `--dry-run`.
6. UDT definitions change root down: a parent type (`typeId`) and any type embedded as a
   member are written and verified before the types that depend on them.
   Write types only with `ign tag udt-type` and the `set-udt-*` verbs, never by importing a
   `_types_` body: an import renames colliding child members to `<name>_duplicate_N`.
7. Before editing an existing UDT type, list the affected types and instances and get the
   user's approval; write nothing until then. Procedure: `references/udt-change-procedure.md`.
8. Always state an alarm's `mode` and `setpointA`: the defaults make an "equal to 0" alarm that
   is active on most integer tags at rest.

## Tasks

Read the reference for the task; it holds the commands and examples.

| Task | Reference |
|---|---|
| Which `ign tag` verb does what, full option syntax | `references/cli-verbs.md` |
| Memory, OPC, expression, or reference tags; alarms on a tag; building tags from Python | `references/atomic-tags.md` |
| Create or edit a UDT type definition | `references/udt-change-procedure.md` first (order, impact, approval), then `references/udt-types.md` |
| Create UDT instances | `references/udt-instances.md` |
| Post a `tags/import` body (multi-tag, nested folders, permission-gated providers) | `references/tag-import.md` |
| Set a tag's value | `references/tag-value-write.md` |
| Delete tags, folders, instances, or types | `references/tag-delete.md` |
| Tag read/write permissions | `references/permissions.md` |
| Read alarm rollups (`Alarm Metrics`) | `references/alarm-metrics.md` |
| Find alarm-bearing tags with `system.tag.query` | `references/tag-query-alarm-attribute.md`, `references/tag-query-wildcards.md` |
| Self-driving alarms for building alarm screens without a PLC | `references/alarm-test-bed.md` |

## Gotchas

| Problem area | Reference |
|---|---|
| Members renamed `<name>_duplicate_N` after a parent type gained the same member | `references/udt-change-procedure.md` |
| Instance overrides give bad quality or phantom alarms | `references/udt-instance-overrides.md` |
| Which members need `valueSource`; `typeId` inheritance | `references/udt-member-inheritance.md` |
| Type edit landed on disk but the gateway runs the old shape | `references/udt-scan-merge-semantics.md` |
| Where type and instance files live, scan collision log lines | `references/tag-disk-layout.md` |
| `Float8`/`Float4`/`Int4` wire names vs labels, parameter types | `references/tag-datatype-wire-names.md` |
| Scan behavior and output of tag verbs | `references/scan-after-disk-writes.md` |
