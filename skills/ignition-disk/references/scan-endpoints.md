# Scan endpoints

After any on-disk change, request a scan:

| Changed | Endpoint |
|---|---|
| `projects/**` | `POST /data/api/v1/scan/projects` |
| `config/resources/**` | `POST /data/api/v1/scan/config` |

```
ign api POST /data/api/v1/scan/projects --confirm
ign api POST /data/api/v1/scan/config --confirm
```

Both need the `X-Ignition-API-Token` header, which `ign api` supplies. Both
are idempotent. Call them manually only after a change `ign` did not make
(git checkout or clean, a verb run with `--no-scan`, a failed automatic scan).
`ign` write verbs already scan, so do not add a second scan after them, and
never use a scan as a health check (use `ign api GET /data/api/v1/gateway-info`). Neither takes a
body or query parameters, so a scan applies the gateway's abort collision
policy to anything it re-reads (use the lock below).

## Response

```json
{ "scanActive": true, "lastScanTimestamp": 1700000000000, "lastScanDuration": 12 }
```

`scanActive: true` immediately after the POST means the scan started.

## What `ign` does for you

Every `ign` write verb posts the matching scan after a successful write
(`--scan/--no-scan`, default scan). A failed scan is reported as
`WARNING:` on stderr with exit 0. Treat that as a failure even though the
exit code is 0: the disk write already happened, but the gateway has not
loaded it, so rerun the scan manually and confirm it succeeds. Pass `--no-scan` when the gateway is unreachable.

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
