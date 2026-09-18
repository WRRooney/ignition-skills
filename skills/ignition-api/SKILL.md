---
name: ignition-api
description: Use when the agent needs to call a raw Ignition 8.3 Gateway HTTP endpoint under /data/api/v1/* that no dedicated ign verb wraps (GET, POST, PUT, DELETE, PATCH), fetch or render the gateway's OpenAPI spec and endpoint docs, read the gateway log with ign logs, or inspect and text-patch an alarm pipeline. Triggers include "ign api", "raw API", "GET endpoint", "POST /data/api/v1/...", "scan endpoint", "gateway-info", "openapi fetch", "api reference", "gateway log", "ign logs", "alarm pipeline". Do not use for tags, views, providers, database connections, or components that have their own ign verb, and never for unrelated REST APIs (GitHub, cloud providers).
---

# Ignition raw API via `ign api`

`ign api METHOD PATH` is the only sanctioned way to call the gateway's
`/data/api/v1/*` endpoints. It reads `IGNITION_URL` and `IGNITION_API_TOKEN`
from the process environment or a `.env` file in the current directory, keeps
the token inside a long-lived httpx client, and never puts it on the command
line. Do not use curl, wget, httpx, requests, or ad-hoc Python for gateway
calls: they put the token in argv, shell history, and tool output
(see `references/http-client-ban.md`).

## Command surface

```
ign api METHOD PATH [--json '...' | --file PATH] [--strict] [--confirm] [--dry-run] [--no-color]
```

| Option | Effect |
|---|---|
| `METHOD` | GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS (case-insensitive) |
| `PATH` | Must start with `/`, e.g. `/data/api/v1/gateway-info`. Query params go inline, quoted |
| `--json '{...}'` | Literal JSON body |
| `--file PATH` | JSON body from a file, or `-` for stdin. Mutually exclusive with `--json` |
| `--strict` | Deep body, query, and path validation with openapi-core (needs the `strict` extra) |
| `--confirm` | Skip the tty confirmation prompt for non-GET/HEAD/OPTIONS |
| `--dry-run` | Print `{method, path, body}` and exit 0 without sending |
| `--no-color` | Plain output (NO_COLOR env also works) |

There is no `--query` flag. Put query parameters in the path and quote it:

```
ign api GET '/data/api/v1/tags/export?provider=default&type=json&recursive=true'
```

## Common calls

| Intent | Command |
|---|---|
| Health check | `ign api GET /data/api/v1/gateway-info` |
| Create/modify a config resource | `ign api POST /data/api/v1/resources/ignition/<type> --file body.json` (body is a JSON array, see `references/resources-array-body.md`) |
| Describe a resource type's settings schema | `ign api GET /data/api/v1/resources/type/ignition/<type>` |
| Rescan projects after a disk write | `ign api POST /data/api/v1/scan/projects --confirm` |
| Rescan config after a disk write | `ign api POST /data/api/v1/scan/config --confirm` |
| List loaded alarm pipelines | `ign api GET /data/alarm-notification/api/v1/pipelines` |

## Order of checks

Everything below runs before any network call:

1. Body parsing (`--json`/`--file`).
2. JWE refusal: any nested object carrying all of `ciphertext`, `encrypted_key`,
   `iv`, `protected`, `tag` is rejected as a `Payload error`. Encrypted
   credentials are set in the Gateway web UI, never constructed by tooling.
3. Settings load. A missing or malformed `IGNITION_API_TOKEN` is an `Auth error`.
   The token is the full header value `<name>:<secret>` as shown on the
   gateway's API Tokens page.
4. Path resolver: method and path are checked against the spec at
   `.ign/openapi.json`. If the file is missing it is fetched from the gateway
   on the spot (a few seconds); no prior `ign openapi fetch` is needed.
5. `--strict` validation, if requested.
6. Confirmation prompt for mutating methods when stdin is a tty and `--confirm`
   is absent. In a non-tty shell no prompt fires; still pass `--confirm` only
   after the user authorized the mutation.
7. `--dry-run` short-circuit.

## Error semantics

Errors print `<Label>: <message>` and a `Hint:` line on stderr. Surface both
verbatim; do not paraphrase. Every error path exits 1; success and dry-run
exit 0.

| Label | Cause | Hint |
|---|---|---|
| `Auth error` | 401, or no token loaded | Check `IGNITION_API_TOKEN` (env or `.env`) |
| `Permission error` | 403, token lacks scope | Review token permissions in the Gateway UI |
| `Payload error` | 400, 422, any other 4xx, strict-validation failure, JWE body | Server response body is included |
| `Gateway error` | 5xx | Retry after confirming the gateway is up |
| `Network error` | DNS, refused, timeout | Check `IGNITION_URL` is reachable from this host |
| `Path error` | Path not in `openapi.json` | Check `.ign/api_reference/INDEX.md` |
| `Method error` | Path exists, method not listed | See the path's operations in `INDEX.md` |

Path and Method errors come from the cached spec, not the gateway, so a stale
spec after a gateway upgrade produces false `Path error`s: `ign openapi fetch`
refreshes it.

## Spec and docs: `ign openapi`

| Command | Effect |
|---|---|
| `ign openapi fetch [--gen]` | Refresh the spec at `.ign/openapi.json` (`--gen` also regenerates the client) |
| `ign openapi gen [--force]` | Regenerate the typed client into `.ign/client/`; skips when `.ign/openapi.hash` matches |
| `ign openapi docs` | Render `.ign/api_reference/*.md` from the spec |

None of these is a prerequisite. The first thing that needs the spec (a typed
verb such as `ign provider names`, `ign api` path validation, `ign openapi
docs`) fetches it to `.ign/openapi.json` and, for typed verbs, generates the
client; expect a few seconds and a one-time "Generating API client" line on
stderr. The generator (`openapi-python-client`) is a core dependency of
`ignition-gen-sdk`; there is no extra to install. `fetch` only refreshes after a
gateway upgrade.

`ign openapi docs` writes one markdown file per API tag plus `INDEX.md` (tag
table with endpoint counts) and `AUTH.md` (header auth template). Read
`INDEX.md` first when looking for an endpoint. The state dir defaults to
`./.ign` and is overridden by `IGNITION_STATE_DIR`; gitignore it.

## Gateway log: `ign logs`

`ign logs` wraps `GET /data/api/v1/logs` and is the first-class way to read
gateway-side script errors.

```
ign logs [--search TEXT] [--min-level TRACE|DEBUG|INFO|WARN|ERROR] [--logger NAME]
         [--limit N] [--since-min N] [--stack] [--json]
```

Defaults: `--limit 25`, no stack traces, formatted lines. `--stack` adds trace
lines for ERROR entries; `--json` emits the raw entries. Query it right after
any scan that touched a script; the messages worth recognizing are in
`references/gateway-logs.md`. A gateway restart is also one call
(`references/gateway-restart.md`), but a scan already loads every Perspective
resource, so restart only for state cached independently of disk.

## Alarm pipelines: `ign alarm-pipeline`

Alarm pipelines are the one project resource with no write API; the Designer
owns the block graph. `ign alarm-pipeline` decodes the binary `data.bin` and can
replace whole text entries but never authors a pipeline.

| Command | Effect |
|---|---|
| `ign alarm-pipeline list --project P` | List pipelines on disk (read-only) |
| `ign alarm-pipeline show --project P --name N [--scripts\|--all]` | Print pooled strings; default shows only Jython bodies |
| `ign alarm-pipeline replace-text --project P --name N (--old S --new S \| --old-file F --new-file F) [--dry-run] [--scan/--no-scan]` | Replace a whole pool entry; scans projects afterwards by default |
| `ign alarm-pipeline copy --from-project A --to-project B [--name N ...] [--overwrite] [--scan/--no-scan]` | Copy `data.bin` + `resource.json`, parsing each before writing |

Prove an edit loaded with `ign api GET /data/alarm-notification/api/v1/pipelines`:
a pipeline that fails to deserialize is absent from that list. Format details in
`references/alarm-pipeline-format.md`; what `system.alarm` scripting can and
cannot do with rosters and pipelines in `references/alarm-scripting-surface.md`.

## Do not

- Do not echo `IGNITION_API_TOKEN` or `.env` contents, and do not build raw
  HTTP calls in any other tool.
- Do not `PUT /data/api/v1/projects/<name>` with a partial body; it is a full
  replace (`references/put-projects-full-replace.md`).
- Do not send a bare object to `POST`/`PUT /resources/ignition/<type>`; wrap it
  in an array.
- Do not construct JWE credential blobs; `ign api` refuses them.
- Do not invent flags. The surface above is complete.

## References

| File | Summary |
|---|---|
| `references/http-client-ban.md` | Why curl/wget/httpx/requests are banned for gateway calls |
| `references/resources-array-body.md` | Resources API wants a JSON array body; element shape; signatures; which read paths answer; live registration |
| `references/put-projects-full-replace.md` | `PUT /projects/{name}` resets omitted fields; create via `POST /projects`; recovery |
| `references/audit-log-filters.md` | `system.util.queryAuditLog` filter behavior on the 8.3 database profile |
| `references/alarm-pipeline-format.md` | `data.bin` binary layout and why `replace-text` is safe |
| `references/alarm-scripting-surface.md` | `system.alarm` rosters and pipelines: what exists in 8.3, what does not, how to verify |
| `references/gateway-logs.md` | `ign logs` as the first diagnostic: messages to recognize, persistence, proving a script ran |
| `references/gateway-restart.md` | Restart over REST, why `pending: []` says nothing, when a restart is actually needed |
