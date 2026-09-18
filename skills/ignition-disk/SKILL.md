---
name: ignition-disk
description: Use when the agent needs to READ or locate an Ignition 8.3 gateway file on disk, such as a config resource under config/resources/<layer>/**, a Perspective view.json, page-config, session-props, project script, named query, style class, or project.json under projects/<name>/**, understand the config layer chain (system, external, core, local), read resource.json metadata, or trigger a gateway scan after a write. Triggers include "config/resources", "core layer", "local layer", "resource.json", "view.json", "what's in this view", "project layout", "scan/projects", "scan/config", "rescan". Read-only: for creating or editing any of these files use the matching ign verb. Do not use for unrelated files, gateway logs (use ign logs), or SDK source code.
---

# Gateway files on disk: read, locate, rescan

The gateway data directory holds two trees that `ign` manages:
`config/resources/**` (gateway configuration) and `projects/**` (project
resources). This skill covers reading them, knowing where each resource
lives, and telling the gateway to rescan. It never writes.

## The sole-writer rule

Only `ign` verbs write under `config/resources/**` and `projects/**`. Do not
use Write or Edit tools, heredocs, `sed -i`, `cp`, `mv`, or Python file IO on
those paths. If a needed shape is not expressible with an existing verb, the
fix is a new option or model in the SDK, never a hand-written file. Reasons
and the full list of banned vectors are in `references/sole-writer-rule.md`.

## Config layers

`config/resources/<layer>/` is a chain. Each layer has a `config-mode.json`
with `title`, `description`, `enabled`, `inheritable`, `parent`.

| Layer | Parent | Inheritable | Role |
|---|---|---|---|
| `system` | none | yes | Base defaults shipped with the gateway; read-only |
| `external` | `system` | yes | Externally managed configuration |
| `core` | `external` | yes | Locally managed configuration; where nearly everything lives and the layer `ign` writes |
| `local` | `core` | no | Instance-unique settings (keystores, UUIDs); not synced to a redundant pair |

`ign` refuses writes under `config/resources/local/` (layer guard). Portable
settings belong in `core`.

## Config resource pattern

```
config/resources/<layer>/<module-id>/<resource-type>/<resource-name>/
  config.json     the payload (some types use other files; themes have index.css and variables.css)
  resource.json   metadata
```

| Module id | Resource types (examples) |
|---|---|
| `ignition` | `tag-provider`, `tag-definition/<provider>/...`, `tag-type-definition/<provider>/...`, `database-connection`, `database-driver`, `database-translator`, `alarm-journal`, `audit-profile`, `identity-provider`, `user-source`, `security-levels`, `opc-connection`, `schedule`, `api-token`, `system-properties`, `images` |
| `com.inductiveautomation.perspective` | `themes/<name>/` (`config.json`, `index.css`, `variables.css`) |
| `com.inductiveautomation.opcua` | server settings; keystores live in `local` |
| `com.inductiveautomation.historian` | historian profiles |
| other modules | their own `<module-id>/<type>/<name>/` trees |

Tag definitions are keyed by provider: `ignition/tag-definition/default/...`
holds the `default` provider's tags and `tag-type-definition/default/...` its
UDTs.

## Project layout

`projects/<name>/project.json` holds `title`, `description`, `enabled`,
`inheritable`, `parent`. A child inherits every resource of its parent chain.

| Resource | Path under `projects/<name>/` | Payload files | Writer |
|---|---|---|---|
| Perspective view | `com.inductiveautomation.perspective/views/<View/Path>/` | `view.json`, `resource.json` (one folder per view; nested folders are view folders) | `ign view` |
| Page config (routes, docks) | `com.inductiveautomation.perspective/page-config/` | `config.json`, `resource.json` | `ign page` |
| Session props | `com.inductiveautomation.perspective/session-props/` | `props.json`, `resource.json` | `ign session-props` |
| Style classes | `com.inductiveautomation.perspective/style-classes/<Path>/` | `style.json`, `resource.json` | `ign style-class` |
| Project stylesheet | `com.inductiveautomation.perspective/stylesheet/` | `stylesheet.css`, `resource.json` | `ign stylesheet` |
| Library scripts | `ignition/script-python/<pkg>/<module>/` | `code.py`, `resource.json` (package dirs have `files: []`) | `ign script` |
| Named queries | `ignition/named-query/<Path>/` | `query.sql`, `resource.json` (parameters, database, caching live in `attributes`) | `ign named-query` |
| Global props | `ignition/global-props/` | gateway-initialized on project creation | none |
| Alarm pipelines | `com.inductiveautomation.alarm-notification/alarm-pipelines/<Name>/` | `data.bin` (binary), `resource.json` | Designer; `ign alarm-pipeline` for text edits |

Themes are config resources, not project resources (`ign theme`).

## `resource.json` fields

```json
{
  "scope": "G",
  "version": 1,
  "restricted": false,
  "overridable": true,
  "files": ["view.json"],
  "attributes": {}
}
```

| Field | Meaning |
|---|---|
| `scope` | Where the resource applies: `A` all, `G` gateway, `D` designer/client, `DG` both. Perspective resources are `G`, library scripts `A`, named queries `DG` |
| `version` | Resource format version |
| `restricted` | Requires elevated permission to view |
| `overridable` | A child project may override it |
| `files` | Payload file names in the folder |
| `attributes` | Type-specific settings plus gateway-stamped `lastModification`, `lastModificationSignature`, sometimes `uuid`, `enabled` |

Details in `references/resource-json-metadata.md`.

## Reading

Use the Read tool or `cat` on any path in either tree. Reading is always
safe. Useful checks:

- Which project a route belongs to: read `page-config/config.json` in the
  project and each ancestor named by `parent`.
- Why a view renders a dashed placeholder: a view folder nested under a
  folder that is itself a view (`views/A/view.json` and `views/A/B/view.json`)
  is invalid and fails silently.
- Whether a child shadows its parent: an empty `page-config/` or
  `session-props/` directory in the child is still a resource and hides the
  parent's entirely (`references/resource-inheritance-and-reload.md`).

## Scans

The gateway notices disk changes only when told. `ign` write verbs scan for
you by default (`--no-scan` to skip). After any other write, or to force a
reload, call the scan endpoints through `ign api`:

```
ign api POST /data/api/v1/scan/projects --confirm    # projects/** changed
ign api POST /data/api/v1/scan/config --confirm      # config/resources/** changed
```

Both return `{scanActive, lastScanTimestamp, lastScanDuration}`;
`scanActive: true` right after the POST means the scan started. A scan loads
everything in Perspective scope; a change that still does not show is a
malformed resource or a runtime error in `ign logs`, not a reload gap. Scan
behavior, the config scan lock, and gateway-scope script reload are in
`references/scan-endpoints.md`.

## Do not

- Do not write, copy, move, or delete anything under `config/resources/**` or
  `projects/**` except through an `ign` verb.
- Do not read `.env` or echo `IGNITION_API_TOKEN`.
- Do not call the scan endpoints with curl or another HTTP client.
- Do not treat a missing subdirectory as a reason to `mkdir`; write verbs
  create missing subdirectories under an existing project themselves
  (`references/sole-writer-rule.md`).

## References

| File | Summary |
|---|---|
| `references/sole-writer-rule.md` | Why only `ign` writes gateway files, banned vectors, auto-scaffold behavior |
| `references/scan-endpoints.md` | Scan endpoints, response shape, config scan lock, what scans do not reload |
| `references/resource-inheritance-and-reload.md` | Per-resource inheritance of page-config and session-props, empty-directory shadowing, script reload scope |
| `references/resource-json-metadata.md` | `resource.json` fields and gateway-stamped attributes |
