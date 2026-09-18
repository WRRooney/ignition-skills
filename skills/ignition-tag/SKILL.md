---
name: ignition-tag
description: |
  Use when the user wants to author, preview, push, import, patch or delete Ignition 8.3 tags with the `ign tag` verbs: memory/OPC/expression tags, alarms on tags, UDT type definitions, UDT instances, member property patches, tag value writes, and the verification steps around them.
  Positive triggers: "push tag", "build tag", "memory tag", "OPC tag at", "tag at default", "preview tag JSON", "Tanks/T01", "dataType Float8", "UDT", "udt-type", "udt-instance", "UDT instance override", "set a tag value", "tags/import", "alarm on a tag", "Alarm Metrics", "delete tag".
  Do not trigger for: git tag, html tag, image alt tag, Docker image tags, tag providers themselves (use ignition-provider), Perspective tag bindings inside a view (use ignition-view).
---

## Verb map

| Intent | Command |
|---|---|
| Preview or validate tag JSON, no gateway | `ign tag build [--file F]` |
| Push atomic tags | `ign tag push --provider P --path X [--file F] [--backend auto\|api\|disk] [--collision-policy ...] [--dry-run] [--no-scan]` |
| POST an arbitrary `tags/import` body (multi-tag, instances, value writes) | `ign tag import --file F --provider P [--path X] [--collision-policy ...] [--type json] [--dry-run] [--confirm] [--no-scan]` |
| Author a UDT type definition (disk only) | `ign tag udt-type --file F --provider P --path X [--dry-run] [--no-scan]` |
| Author UDT instances on disk (replaces the folder's `udts.json`) | `ign tag udt-instance --file F --provider P --path X [--dry-run] [--no-scan]` |
| Patch one property on members of an existing type file | `ign tag set-udt-member-prop --prop K --value V --provider P --path X [--where K=V] [--dry-run] [--no-scan]` |
| Patch one property on the type node itself | `ign tag set-udt-type-prop --type NAME --prop K --value V --provider P --path X [--dry-run] [--no-scan]` |
| Delete a tag, folder or instance directory | `ign tag delete --provider P --path X [--kind instance\|type] [--dry-run] [--no-scan]` |

Every option above exists in `--help`; do not invent others. `--provider` defaults to `default` (or `IGNITION_TAG_PROVIDER`). Append `--dry-run` first on anything that writes. Surface `ign`'s stdout and any `Error:` / `Hint:` stderr lines verbatim.

Without `--file`, `build` and `push` operate on a built-in demo OPC tag named `SmokeTestLevel`; that is a smoke test, not an authoring path.

## Authoring an atomic tag

Write the tag JSON to a file and pass `--file`. The file may be a single tag object, a JSON list, or a full import body. Each tag is validated through the `Tag` model before anything is sent.

```json
{"name": "Level", "tagType": "AtomicTag", "dataType": "Float8",
 "valueSource": "memory", "value": 42.0, "engUnit": "%"}
```

```bash
ign tag build --file level.json                                   # prints the tags/import body
ign tag push --provider default --path Tanks/T01 --file level.json --dry-run
ign tag push --provider default --path Tanks/T01 --file level.json
```

Rules the model enforces:

- A standalone `AtomicTag` requires both `dataType` and `valueSource`. Only UDT member tags and folders may omit them.
- `dataType` literals: `Float4` (4-byte float), `Float8` (double), `Int4`, `Boolean`, `String`, and the rest of the Ignition set (`references/tag-datatype-wire-names.md`).
- `valueSource`: `memory`, `opc` (with `opcServer` + `opcItemPath`), `expr` (with `expression`), `reference` (with `sourceTagPath`), `db`.
- Names are sanitized: characters outside letters, digits, `_ ()':-` are dropped, and a name not starting with a letter or underscore gets a leading underscore.
- A `UdtType` node fed to `build` or `push` is rejected; use `udt-type`.

`--backend auto` (the default) tries the API and falls back to a disk write only on a 5xx. Use `--backend api` when the data dir is not mounted. `--collision-policy` defaults to `Overwrite` (the file is the intended end state); `MergeOverwrite` keeps members the file no longer lists.

### Alarms on a tag

Add an `alarms` array. Serialized values, not Python enum names:

```json
{"name": "Level", "tagType": "AtomicTag", "dataType": "Float8", "valueSource": "memory", "value": 0.0,
 "alarms": [{"name": "HighLevel", "priority": "High", "mode": "AboveValue", "setpointA": 90.0}]}
```

- `mode`: `AboveValue`, `BelowValue`, `BetweenValues`, `OutsideValues`, `Equality`, `Inequality`, `OutOfEngRange`, `BadQuality`, `AnyChange`, `Bit`.
- `priority`: `Diagnostic`, `Low`, `Medium`, `High`, `Critical`.
- Setpoints are `setpointA` and `setpointB` (range modes), never `setpoint`.
- Defaults the model fills: `enabled: true`, `inclusiveA: true`, `ackMode: "Manual"`, `priority: "Low"`, `mode: "Equality"`, `setpointA: 0.0`. Note that an unspecified alarm is therefore "equal to 0", which is active for most integer tags at rest. Always state `mode` and `setpointA`.

## UDT type definitions

A UDT type is a different resource from tags: it lives under `config/resources/core/ignition/tag-type-definition/<provider>/<path>/udts.json` (paths, sidecars and file formats in `references/tag-disk-layout.md`). There is no API import path for it, so `udt-type` is disk-only and scans `/scan/config` after writing.

```json
{"name": "Pump", "tagType": "UdtType",
 "parameters": {"DeviceRoot": {"dataType": "String", "value": null}},
 "tags": [
   {"name": "Running", "tagType": "AtomicTag", "dataType": "Boolean", "valueSource": "opc",
    "opcServer": "Ignition OPC UA Server", "opcItemPath": "ns=1;s=[{DeviceRoot}]Running"},
   {"name": "Speed", "tagType": "AtomicTag", "dataType": "Float4", "valueSource": "memory", "value": 0.0,
    "alarms": [{"name": "Overspeed", "mode": "AboveValue", "priority": "High", "setpointA": 1800.0}]},
   {"name": "Diagnostics", "tagType": "Folder", "tags": []}
 ]}
```

```bash
ign tag udt-type --provider default --path Equipment --file pump.json --dry-run   # prints a JSON array
ign tag udt-type --provider default --path Equipment --file pump.json
```

Shape rules:

- `--file` is one `UdtType` object or a list. `--dry-run` always prints an array, even for one type; that is the file shape, not a bug.
- `typeId` on a type is its parent type path (inheritance). A member overriding an inherited member carries only the changed keys; a member with no parent supplying it still needs `dataType` and `valueSource`. See `references/udt-member-inheritance.md`.
- Custom metadata is flat `meta_*` keys on the type, instance or member node. The model rejects any other unknown key as a typo.
- `parameters` is a dict keyed by parameter name: `{"dataType": "String", "value": <default or null>}`. Parameter `dataType` literals are their own set (`String`, `Float`, ...), not the member-tag `Float4`/`Float8` set. Members reference a parameter with `{ParamName}`; alarm properties may be bound as `{"bindType": "UDTParameter", "value": "{Message}"}`.
- A `Folder` member carries no `dataType` or `valueSource`.
- `udt-type` writes only the leaf folder for `--path`. Nested type paths need each parent folder to exist as its own resource, so keep type trees flat or create parent folders in the Designer first.
- On the gateway the type appears under the synthetic `_types_/<path>/` folder.

Verify a landed type (there is no browse endpoint; `export` and `import` are the only tag endpoints):

```bash
ign api GET "/data/api/v1/tags/export?provider=default&path=_types_%2FEquipment&recursive=true&includeUdts=true"
```

### Editing an existing type

`udt-type --file` replaces the whole `udts.json` from the input, so a partial file silently drops sibling types in the same folder. For a targeted change use the patch verbs, which read the file, change only what matches, re-validate every type and write the full list back:

```bash
ign tag set-udt-member-prop --provider default --path Equipment --prop opcServer --value "Plant OPC" --where valueSource=opc --dry-run
ign tag set-udt-type-prop --provider default --path Equipment --type Pump --prop meta_area --value '"Area1"'
```

`--value` is parsed as JSON when possible, else kept as a string. A no-op prints `No change:` and skips the write. When you must rewrite a whole family file, diff the list of type names before and after.

The gateway's config scan merges member additions into a loaded type but silently refuses a member kind change (for example `AtomicTag` to `UdtInstance`): the file shows the new shape, the gateway keeps running the old one. Procedure in `references/udt-scan-merge-semantics.md`.

## UDT instances

```json
[{"name": "Pump01", "tagType": "UdtInstance", "typeId": "Pump",
  "parameters": {"DeviceRoot": {"dataType": "String", "value": "Area1/Pump01"}}}]
```

Two write paths:

- `ign tag import --file instances.json --provider default --path Area1` posts through `/tags/import` (merge-capable, registers live). `--dry-run` also resolves each `typeId` against the on-disk type definitions when the data dir is visible and lists issues.
- `ign tag udt-instance --file instances.json --provider default --path Area1` writes `tag-definition/default/Area1/udts.json` on disk. It replaces the folder's instance list, so include every instance the folder should end up with.

`tag push` rejects `UdtInstance` nodes unless `--backend api`, because the disk path writes `tags.json`, which is the wrong file for instances.

Instance overrides fail silently in three ways (bad quality or phantom alarms, never an error): an override leaf must restate `valueSource`; an `alarms` override replaces the whole alarm and omitted keys take Ignition defaults, not the type's; an undriven alarm bit counts as active. Full rules in `references/udt-instance-overrides.md`.

## Import body rules

`tag import` sends the file body (after the list wrap below) to `/tags/import`:

- The documented body is the `{"tags": [...]}` object form. `--file` also accepts a bare JSON list of tags and wraps it as `{"tags": [...]}` before sending, because the gateway rejects a bare top-level array with `Not a JSON Object`.
- For multi-instance imports into a nested folder, embed the folder hierarchy in the body (`{"tags":[{"name":"Area1","tagType":"Folder","tags":[...]}]}`) and omit `--path`. Combining `--path` with a folder-bearing body makes the gateway create `<Folder>_duplicate_N` collision folders.
- Tags imported this way register live; the default `--scan` keeps disk state aligned.
- A provider whose `editPermissions` require the `Authenticated` security level rejects token imports with `Insufficient Tag Provider Edit Permissions` (`qualitySubCode` 514). Use the disk verbs plus scan for that provider; disk writes are not permission-checked. Check with `ign provider get <name>`.

## Writing a tag value

There is no `/tags/write` or `/tags/read` endpoint. A minimal `{name, tagType, value}` import with `collisionPolicy=Overwrite` sets the value and leaves the rest of the tag's configuration intact. Recipe and caveats in `references/tag-value-write.md`. `/tags/export` returns configuration only, never runtime quality, so a headless "does this member resolve Good" check is not possible through the API.

## Deleting

```bash
ign tag delete --provider default --path Tanks/T01 --dry-run     # prints the directory
ign tag delete --provider default --path Tanks/T01               # tag-definition dir + scan
ign tag delete --provider default --path Equipment --kind type   # tag-type-definition dir + scan
```

Removes the whole directory (`tags.json` and/or `udts.json` plus `unary-resource.json`); the gateway drops the tags on the scan. There is no REST delete for tags, so this is the only sanctioned remover. Confirm the path with the user before running without `--dry-run`.

## Reading alarm state through tags

Every folder and UDT instance exposes rollups as dot-addressed tag properties: `[default]Area1/Alarm Metrics.ActiveUnackCount`. The slash form returns bad quality. There is no plain `ActiveCount`. Details and the full property list in `references/alarm-metrics.md`. To find alarm-bearing tags from a script, `system.tag.query` takes an `attributes` condition with the value `alarm`; see `references/tag-query-alarm-attribute.md`. Its `path: "<root>/*"` wildcard is recursive and contains-match (`references/tag-query-wildcards.md`). For a PLC-free set of alarms that raise and clear on their own while building alarm screens, see `references/alarm-test-bed.md`.

## Library path

For generated tag sets, build with `ignition_gen_sdk.TagBuilder` (`.name().datatype().opc(...)|.memory()|.expression()|.reference()|.alarm(Alarm(...))|.history(...)|.build()`) or the models in `ignition_gen_sdk.models.tags` (`Tag`, `UdtType`, `UdtInstance`, `Alarm`), write the JSON to a file, and hand it to the CLI. Generators belong in `.ign_tools/` and run through `ign tools run`.

## References

| File | Summary |
|---|---|
| `references/udt-instance-overrides.md` | Three silent instance-override failures: explicit `valueSource`, alarm override replaces, undriven alarm bits |
| `references/udt-member-inheritance.md` | `typeId` inheritance, which members need `valueSource`, standalone vs member rules, indirect binding forms |
| `references/udt-scan-merge-semantics.md` | Scan merges additions but refuses kind changes; whole-file edits drop siblings; recovery procedure |
| `references/tag-value-write.md` | Value writes via `/tags/import`, body shape, folder-vs-path rule, provider permission gate |
| `references/tag-query-alarm-attribute.md` | `system.tag.query` attribute filter values and what the query returns |
| `references/alarm-metrics.md` | Alarm Metrics property names, dot addressing, null behavior, binding pattern |
| `references/scan-after-disk-writes.md` | Pointer to the canonical scan reference in ignition-disk, plus tag-verb scan specifics and output |
| `references/tag-disk-layout.md` | Type vs instance resource trees, `unary-resource.json`, `tags.json` vs `udts.json`, `usr` envelope, scan collision log lines |
| `references/tag-datatype-wire-names.md` | `Float8`/`Float4`/`Int4` wire names vs model labels, parameter type set, value echoes |
| `references/tag-query-wildcards.md` | `system.tag.query` `*` is recursive and contains-match; post-filter, `SubType` hierarchy, auth caveat |
| `references/alarm-test-bed.md` | Six clock-driven expression tags that raise and clear every priority without a PLC |
