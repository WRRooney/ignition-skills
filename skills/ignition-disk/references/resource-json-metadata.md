# `resource.json` metadata

Every resource folder in both trees has a `resource.json` next to its
payload files.

## Fields

| Field | Type | Meaning |
|---|---|---|
| `scope` | string | `A` all, `G` gateway only, `D` designer/client, `DG` designer and gateway. Views, page-config, session-props, and style classes are `G`; library scripts are `A`; named queries are `DG` |
| `description` | string | Optional; present on config resources |
| `version` | int | Resource format version (views 1, named queries 2) |
| `restricted` | bool | Needs elevated permission to view |
| `overridable` | bool | A child project may override the resource |
| `files` | list | Payload file names in the folder; a script package directory has `[]` |
| `attributes` | object | Type-specific settings plus gateway-stamped metadata |

## Type-specific attributes

Named queries store their configuration here rather than in a separate
payload file: `type`, `database`, `parameters` (each `{type, identifier,
sqlType}`), `cacheEnabled`, `cacheAmount`, `cacheUnit`, `fallbackEnabled`,
`fallbackValue`, `maxReturnSize`, `useMaxReturnSize`, `autoBatchEnabled`,
`permissions`, `enabled`. Script modules carry `hintScope`. Config
resources such as database connections carry `enabled` and `uuid`.

## Gateway-stamped attributes

Any save through the Designer or a gateway-mediated write adds:

```json
"attributes": {
  "lastModificationSignature": "<sha256>",
  "lastModification": { "actor": "<user>", "timestamp": "2026-01-01T00:00:00Z" }
}
```

These change on every save and carry no configuration. When comparing a
resource against a manifest baseline, ignore them. `ign` writes leave an
existing `attributes` block alone apart from their own `lastModification`
stamp; only the gateway regenerates the signature.

## Views

A view folder holds `view.json` and `resource.json`, with `files:
["view.json"]` and usually `attributes: {}`. `view.json` itself has no
`attributes` block. `files` must list only files that exist: a manifest that
names `thumbnail.png` when none was written logs `Error creating dataFile ...
NoSuchFileException` on every scan, and the running gateway keeps expecting
the file after the manifest is fixed until a restart. The Designer adds and
lists the thumbnail on its first save. A folder whose parent folder is also a view is invalid;
the nested view renders as a dashed placeholder and validation does not
flag it.

## Designer emit policy

Match these in serializers or accept churn on every Designer save: keys
ASCII-sorted (`udts.json` forces `tags` last), UDT member and instance arrays
name-sorted, `>`, `=`, `&`, `'` escaped Gson HTML-safe style, non-ASCII written
literally, whole-number history props as ints (`historyMaxAge: 1`), CRLF
inside expression strings. Explicit `null` for `position.basis/grow/shrink`
and `props.direction` is deleted on round-trip (emit with `exclude_none`), and
Perspective defaults (`direction: "row"`, `basis: "auto"`, `grow: 0`,
`params: {}`, `overflow: "auto"`) are best not emitted. `modules.json` gains
Designer dark-mode entries; ignore them.
