# Tag resources on disk: paths, sidecars, file formats

UDT *types* and tag *instances* live in different resource trees with
different sidecar files. `ign tag udt-type`, `udt-instance`, `push --backend disk`
and `delete` write these; read them to learn a shape, never edit them by hand.

| Thing | Path under `config/resources/core/` | Data file | Sidecar |
|---|---|---|---|
| UDT type | `ignition/tag-type-definition/<provider>/<path>/` | `udts.json` | `unary-resource.json` |
| UDT instances in a folder | `ignition/tag-definition/<provider>/<path>/` | `udts.json` | `unary-resource.json` |
| Atomic tags in a folder | `ignition/tag-definition/<provider>/<path>/` | `tags.json` | `unary-resource.json` |
| Intermediate type folder | `ignition/tag-type-definition/<provider>/<parent>/` | none | `unary-resource.json` with `files: []` |

The sidecar is `{"scope": "G", "version": 1, "restricted": false,
"overridable": true, "files": [...], "attributes": {"config": {}}}`; no
signature. Path segments are percent-encoded per segment (`light:0` becomes
`light%3a0`); split on `/` first, then encode each segment.

## File formats

- `tags.json` under a standard provider is a flat array of tag objects. The
  `usr` envelope appears only under managed providers (MQTT drivers), where it
  is the user-override layer over driver-supplied config; wrapping
  standard-provider files in `usr` is wrong.
- `udts.json` is always a flat array. An instance file replaces the folder
  wholesale, so include every instance the folder should end up with.
- The Designer writes a meta-only override of an inherited member as
  `"tagType": "AtomicTag"` plus only the changed keys, even when the member is
  a UDT instance (`udt-member-inheritance.md`).
- A member `AtomicTag` inside a type carries `dataType` and `valueSource`;
  `Folder` members carry neither. Parameters are
  `{"<name>": {"dataType": "String", "value": "..."}}`; `exclude_none` drops a
  `"value": null` default and the gateway tolerates the absence.

## Traps

- A type at `tag-type-definition/default/Base/Pump/udts.json` without a
  `unary-resource.json` in `Base/` never appears: the hierarchy does not
  resolve. `udt-type` writes only the leaf folder, so keep type trees flat or
  create parent folders in the Designer first.
- Looking for a type at its instance-style path in an export reports
  `tagType: "Unknown"`.
- `GET /data/api/v1/resources/ignition/tag-type-definition/...` is rejected;
  there is no per-resource read. Read back with
  `/tags/export?provider=default&recursive=true&includeUdts=true`, where types
  appear under a synthetic `_types_/<path>/` folder.
- Every config scan can log `Tag already exists, and 'abort' collision policy
  has been specified` for types in a secured provider; the scan-driven edit is
  submitted with policy abort. When abort bites for real, instances export as
  `tagType: Unknown` with no members. Only `/tags/import` accepts
  `collisionPolicy`; tooling defaults to `Overwrite`.

## Verify

A 2xx `/scan/config`, then the export above. A dry run of instance imports can
resolve each `typeId` against the `<path>/<name>` pairs found by globbing
`tag-type-definition/<provider>/**/udts.json`; `ign tag import --dry-run` does
this when the data dir is visible.
