# UDT type definitions

Plan every addition or edit with `udt-change-procedure.md` first: write order is root down,
and edits to existing types need an impact check and the user's approval.

A UDT type is a different resource from tags: it lives under `config/resources/core/ignition/tag-type-definition/<provider>/<path>/udts.json` (paths, sidecars and file formats in `tag-disk-layout.md`). `udt-type` is disk-only and scans `/scan/config` after writing. `/tags/import` also accepts a `_types_` body, but do not use it for types: it renames colliding child members to `<name>_duplicate_N` and drops instance overrides (`udt-change-procedure.md`).

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
- `typeId` on a type is its parent type path (inheritance). A member overriding an inherited member carries only the changed keys; a member with no parent supplying it still needs `dataType` and `valueSource`. See `udt-member-inheritance.md`.
- Custom metadata is flat `meta_*` keys on the type, instance or member node. The model rejects any other unknown key as a typo.
- `parameters` is a dict keyed by parameter name: `{"dataType": "String", "value": <default or null>}`. Parameter `dataType` literals are their own set (`String`, `Float`, ...), not the member-tag `Float4`/`Float8` set. Members reference a parameter with `{ParamName}`; alarm properties may be bound as `{"bindType": "UDTParameter", "value": "{Message}"}`.
- A `Folder` member carries no `dataType` or `valueSource`.
- `udt-type` writes only the leaf folder for `--path`. Nested type paths need each parent folder to exist as its own resource, so keep type trees flat or create parent folders in the Designer first.
- On the gateway the type appears under the synthetic `_types_/<path>/` folder.

Verify a landed type (there is no browse endpoint; `export` and `import` are the only tag endpoints):

```bash
ign api GET "/data/api/v1/tags/export?provider=default&path=_types_%2FEquipment&recursive=true&includeUdts=true&type=json"
```

## Editing an existing type

`udt-type --file` replaces the whole `udts.json` from the input, so a partial file silently drops sibling types in the same folder. For a targeted change use the patch verbs, which read the file, change only what matches, re-validate every type and write the full list back:

```bash
ign tag set-udt-member-prop --provider default --path Equipment --prop opcServer --value "Plant OPC" --where valueSource=opc --dry-run
ign tag set-udt-type-prop --provider default --path Equipment --type Pump --prop meta_area --value '"Area1"'
```

`--value` is parsed as JSON when possible, else kept as a string. A no-op prints `No change:` and skips the write. When you must rewrite a whole family file, diff the list of type names before and after.

The gateway's config scan merges member additions into a loaded type but silently refuses a member kind change (for example `AtomicTag` to `UdtInstance`): the file shows the new shape, the gateway keeps running the old one. Procedure in `udt-scan-merge-semantics.md`.
