# Scan endpoints

The gateway keeps an in-memory picture of both trees and refreshes it on a
scheduled tick, on restart, or when asked. After any on-disk change, ask:

| Changed | Endpoint |
|---|---|
| `projects/**` | `POST /data/api/v1/scan/projects` |
| `config/resources/**` | `POST /data/api/v1/scan/config` |

```
ign api POST /data/api/v1/scan/projects --confirm
ign api POST /data/api/v1/scan/config --confirm
```

Both need the `X-Ignition-API-Token` header, which `ign api` supplies. Both
are idempotent and cheap; scan even after a one-file change. Neither takes a
body or query parameters; only `/tags/import` accepts a `collisionPolicy`, so
a scan applies the gateway's internal abort policy to anything it re-reads
(hence the lock below).

## Response

```json
{ "scanActive": true, "lastScanTimestamp": 1700000000000, "lastScanDuration": 12 }
```

`scanActive: true` immediately after the POST means the scan started.

## What `ign` does for you

Every `ign` write verb posts the matching scan after a successful write
(`--scan/--no-scan`, default scan). A failed scan is reported as
`WARNING:` on stderr with exit 0; the disk write already happened, so rerun
the scan manually. Pass `--no-scan` when the gateway is unreachable.

## Config scan lock

For config writes the SDK can hold a scan lock:
`POST /data/api/v1/scan-lock/config` with
`{"acquireTimeout": 10, "holdTimeout": 60}`. While held, the gateway queues
other config changes, so an external write plus `scan/config` is atomic from
the gateway's view and avoids mid-write pickup and "abort collision policy"
errors. The next `scan/config` releases the lock; if it never comes, the lock
expires after `holdTimeout` seconds. Always pair acquire with a scan.

## What a scan does and does not do

- `/scan/projects` loads everything in Perspective scope: views, pages,
  session props, style classes, and project library `code.py` modules. There
  is no reload gate and no signature gate. When a resource does not behave
  after a scan it is malformed or has a runtime error; read
  `ign logs --min-level ERROR --stack` before reaching for a restart. Config
  resources created through the resources API register live with no scan.
- It reloads project library scripts for Perspective scope but not for
  gateway scope (tag event scripts, gateway timer scripts); see
  `resource-inheritance-and-reload.md`.
- It merges UDT member additions but silently refuses a member kind change
  (ignition-tag skill, `udt-scan-merge-semantics`).
- It does not fix a child project that shadows its parent with an empty
  resource directory; delete the directory instead.
- `PUT /data/api/v1/projects/<name>` is not a scan and does not recompile
  scripts.
