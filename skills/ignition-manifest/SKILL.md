---
name: ignition-manifest
description: Use when the agent needs to know whether an Ignition resource changed since ign last pushed or wrote it, run ign diff against the push manifest, inspect the manifest files under .ign/manifest/, understand the manifest entry schema or its sha256 rule, or decide which resource.json metadata to ignore when comparing payloads. Triggers include "manifest", "ign diff", "diff vs last push", "changed since push", "sha256", "idempotent push", "no changes since", "lastModificationSignature". Do not use for plain git diff, for diffs between two gateways, or for comparing files unrelated to a manifest entry.
---

# Push manifest and `ign diff`

Every successful `ign` write or push records what it sent in a manifest, one
JSON file per resource type. `ign diff` compares a payload you supply against
that record and reports whether a re-push would be a no-op. There is no
`manifest` subcommand; `diff` is a top-level command.

## Command surface

```
ign diff RESOURCE_TYPE RESOURCE_ID (--current-file PATH | --from-stdin) [--json] [--no-color]
```

| Argument / option | Meaning |
|---|---|
| `RESOURCE_TYPE` | `tags`, `views`, `providers`, `database-connections` |
| `RESOURCE_ID` | `<provider>/<path>` for tags, `<project>/<view path>` for views, `<name>` for providers and database connections |
| `--current-file PATH` | JSON file holding the current payload |
| `--from-stdin` | Read the current payload from stdin |
| `--json` | Machine-readable diff instead of a unified diff |
| `--no-color` | Plain output |

Exactly one payload source is required. `ign diff` never fetches the live
resource for you; you supply the JSON to compare.

## Exit codes

| Exit | Meaning |
|---|---|
| 0 | sha256 match; the payload is unchanged since the last push |
| 1 | Differences exist; the diff is printed |
| 2 | No manifest entry for this resource (never pushed from this state dir, or a dry run) |

Report the exit code alongside the diff output; a scripted caller keys off it.

## Examples

```
ign diff tags default/Tanks/T01 --current-file /tmp/t01.json
ign diff views Demo/Main/Overview --from-stdin < view.json
ign diff database-connections Demo_DB --current-file demo_db.json --json
```

## Where the manifest lives

`<state-dir>/manifest/<resource-type>.json`, where the state dir is `./.ign`
relative to the working directory unless `IGNITION_STATE_DIR` overrides it.
The files are tooling-local state; gitignore `.ign/`.

Files you may see: `tags.json`, `views.json`, `providers.json`,
`database-connections.json`.

## Who writes entries

| Command | Type | Notes |
|---|---|---|
| `ign tag push` | `tags` | id `<provider>/<path>` |
| `ign view write` | `views` | id `<project>/<view path>`; backend `disk` |
| `ign provider create/update/delete` | `providers` | |
| `ign db-conn create/update/delete` | `database-connections` | recorded after the API call and before the scan, so a failed scan keeps the entry; `delete` stores `{}` as a tombstone |

Dry runs never record. Writes are atomic (temp file then rename). Do not edit
manifest files by hand; a corrupt file is silently treated as empty.

## Entry schema

```json
{
  "default/Tanks/T01": {
    "payload": { "...": "..." },
    "sha256": "<64 hex>",
    "timestamp": "2026-01-01T12:00:00+00:00",
    "backend": "api"
  }
}
```

`payload` is a dict or a list, whichever shape the live artifact has (the API
envelope for the `api` backend, the bare disk shape for `disk`). The sha256
is computed over the canonical JSON of that payload, not over file bytes:
`json.dumps(payload, sort_keys=True, separators=(",", ":"))`. Full detail in
`references/manifest-entry-schema.md`.

## Ignore gateway-stamped metadata

When the Designer or any gateway-mediated write saves a resource, the gateway
stamps `resource.json` with:

```json
"attributes": {
  "lastModificationSignature": "<sha256>",
  "lastModification": { "actor": "<user>", "timestamp": "<ISO>" }
}
```

Some resource types add `uuid` or `enabled` here too. These keys change on
every save and say nothing about the resource's content. When building a
`--current-file` from a `resource.json`-style payload, drop the
`attributes` keys above before diffing, or every Designer touch reports a
change. A Perspective `view.json` carries no `attributes` block (that
metadata lives in the sibling `resource.json`), so for views there is
nothing to strip.

## Do not

- Do not prefix with `manifest`; the command is `ign diff ...`.
- Do not compare `manifest.sha256` against `sha256sum` of a file; the file is
  pretty-printed and the hash is canonical. Parse, then re-hash, or let
  `ign diff` do it.
- Do not hand-edit `.ign/manifest/*.json`.
- Do not echo `IGNITION_API_TOKEN`; `ign diff` is offline and needs no token.

## References

| File | Summary |
|---|---|
| `references/manifest-entry-schema.md` | Field-by-field entry schema, id conventions, canonical hashing rule |
