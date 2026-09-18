# Write backends

`ign` writes through one of two backends. Some verbs support both, most support exactly one.

## API backend

HTTP calls under `/data/api/v1/*` with the token in a request header. Changes register live: a tag imported through `/tags/import` exists immediately, a provider created through the resources API starts immediately. No scan is required for the resource itself, though `tag import` and the provider mutations still POST `/scan/config` by default so on-disk state and the gateway stay in step.

Verbs: `tag push --backend api`, `tag import`, `provider *`, `db-conn *`, `alarm-journal *`, `driver *`, `api`, `logs`, `diff`.

Limits: there is no API import path for UDT type definitions, and Perspective resources (views, pages, scripts, themes, style classes) are file-only.

## Data-dir backend

Writes files under `IGNITION_DATA_DIR`:

| Resource | Path written |
|---|---|
| atomic tags | `config/resources/core/ignition/tag-definition/<provider>/<path>/tags.json` + `unary-resource.json` |
| UDT instances | `config/resources/core/ignition/tag-definition/<provider>/<path>/udts.json` + `unary-resource.json` |
| UDT types | `config/resources/core/ignition/tag-type-definition/<provider>/<path>/udts.json` + `unary-resource.json` |
| Perspective resources | `projects/<project>/com.inductiveautomation.perspective/...` |

Writes are atomic per file and are confined to the `core` config layer; `ign` refuses paths that resolve into the `local` layer or outside the resource root. Before a config write that will scan, `ign` acquires the gateway's config scan lock so the write and the scan land as one unit; a failed lock is a warning, not a failure.

After the write, the verb POSTs the matching scan endpoint:

| Files touched | Endpoint |
|---|---|
| `config/resources/**` | `POST /data/api/v1/scan/config` |
| `projects/**` | `POST /data/api/v1/scan/projects` |

Response shape: `{"scanActive": true, "lastScanTimestamp": ..., "lastScanDuration": ...}`. `scanActive: true` right after the POST means the scan started. Without the scan the gateway keeps a stale picture of the disk until its next natural scan tick or a restart. A failed scan prints `WARNING:` on stderr and still exits 0, because the file is already written.

Verbs: `tag udt-type`, `tag udt-instance`, `tag set-udt-member-prop`, `tag set-udt-type-prop`, `tag delete`, `tag push --backend disk`, `view *`, `page *`, `script *`, `session-props *`, `named-query *`, `style-class *`, `stylesheet *`, `theme *`, `alarm-pipeline *`.

## `tag push --backend auto`

The default for `tag push`. It tries the API first and falls back to a disk write only on a 5xx gateway error, then raises a warning naming the disk path and scanning. A 400 (bad payload), 401 (no token) or 403 (missing scope) is not retried on disk, because that would hide the real problem. Pass `--backend api` when the data dir is not mounted so a gateway outage produces a clear error instead of a file written to the wrong machine.

## Deciding which the user has

```bash
ls "${IGNITION_DATA_DIR:-.}/config/resources" "${IGNITION_DATA_DIR:-.}/projects"
```

Both directories present: disk backend available, full verb set. Missing: API-only. Record the answer in `.agents/skills/ignition-local/SKILL.md` so later sessions do not re-probe.

Common host setups:

- Gateway on the same machine, data dir readable: full set.
- Gateway in a container with the data directory bind-mounted to the host: full set; `IGNITION_DATA_DIR` points at the host side of the mount, `IGNITION_URL` at the host-mapped port.
- Gateway on a remote host with only HTTP exposed: API-only.
