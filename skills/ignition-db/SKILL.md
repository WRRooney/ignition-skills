---
name: ignition-db
description: Use when the agent needs to list, inspect, create, update, rename, or delete an Ignition 8.3 database connection (datasource) with ign db-conn, create or inspect an alarm journal profile that stores alarm events into a datasource with ign alarm-journal, or check which JDBC drivers the gateway has with ign driver. Triggers include "database connection", "db-conn", "datasource", "JDBC", "SQLite connection", "MySQL connection", "connectURL", "alarm journal", "alarm history", "queryJournal", "which drivers are installed". Do not use for tag providers, history providers, identity or OAuth providers, or databases unrelated to an Ignition gateway.
---

# Database connections, alarm journals, drivers

All three verb groups talk to the gateway's config resources API through the
SDK's authenticated client. Auth comes from `IGNITION_API_TOKEN` in the
environment or `.env`; never pass it on the command line and never echo it.
Config resources register live: a created connection opens and a created
journal starts logging without a gateway restart.

## `ign db-conn`

| Intent | Command |
|---|---|
| List connections with full config | `ign db-conn list` |
| Names only | `ign db-conn names` |
| One connection | `ign db-conn get <NAME>` |
| Resource-type metadata | `ign db-conn describe` |
| Create | `ign db-conn create --name N --config-file F [--description D] [--enabled/--disabled] [--password-stdin] [--dry-run] [--scan/--no-scan]` |
| Update | `ign db-conn update --name N --config-file F [same options as create]` |
| Delete | `ign db-conn delete --name N [--yes] [--scan/--no-scan]` |
| Bulk delete | `ign db-conn delete-bulk --entries-file F` |
| Rename | `ign db-conn rename --name OLD --new-name NEW` |

Notes on the verbs:

- `--config-file` takes a path or `-` for stdin. The file holds the 25
  `ConnectionConfig` fields (any subset; the gateway back-fills defaults),
  optionally with an outer `backupConfig` sibling. See
  `references/connection-config-shape.md`.
- `describe` returns resource-type metadata (extension points, counts,
  defaults). It is not a field schema; clone `ign db-conn get <existing>` for
  the real shape.
- `update` and `delete` fetch the resource signature first, then act
  (two-call pattern). `delete` prompts unless `--yes`.
- `delete-bulk` wants a JSON list of `{name, signature}` objects.
- `rename` updates cross-resource references (for example alarm journals
  pointing at the old name).
- `create`, `update`, `delete` post `/data/api/v1/scan/config` afterwards
  by default. A failed scan prints `WARNING:` on stderr and still exits 0.
  Pass `--no-scan` when the gateway is unreachable. `delete-bulk` and
  `rename` do not scan.
- `create`, `update`, `delete` record a `database-connections` manifest
  entry for `ign diff` (delete stores an empty payload as a tombstone).
- The driver name in the config file is checked against `ign driver list`
  before any create/update request is sent.

## Passwords

Never put an encrypted credential blob in a config file. Ignition stores
passwords on disk as an AES-256-GCM JWE object; the SDK refuses any payload
that carries the five JWE keys and raises a validation error before any HTTP
call (`references/jwe-refusal.md`).

Plaintext password resolution for `create`/`update`, in order:

1. Config already has a dict-shaped `password`: passed through, then refused
   by the JWE guard.
2. Config has a non-empty plaintext `password` string: used as is.
3. `--password-stdin`: one line read from stdin. Pipe-friendly, no prompt.
4. No flag, stdin is a tty: hidden interactive prompt; injected if non-empty.
5. No flag, not a tty, no `password` key: nothing injected (fine for SQLite,
   H2, or any no-auth driver).

Resolution never errors; the gateway rejects the connection later if the
driver actually needs credentials. Prefer branch 3 in scripts:

```
printf '%s\n' "$DB_PASSWORD" | ign db-conn create --name Demo_DB --config-file demo_db.json --password-stdin
```

`--dry-run` prints the payload and exits 0 before model validation, so it
does not exercise the JWE guard or the driver check. Only the real
create/update path does.

## `ign driver`

| Command | Effect |
|---|---|
| `ign driver list` | Installed JDBC drivers with enabled flag |
| `ign driver describe <NAME>` | One driver: translator, URL format, class name, and more |

Use `describe` to get the `connectURL` template and matching `translator`
before writing a config file. Driver names are exact, for example `SQLite`,
`MySQL`, `'Oracle Database'`.

## `ign alarm-journal`

An alarm journal profile stores alarm events into a datasource so
`system.alarm.queryJournal` and the Alarm Journal Table component return
history. Create the database connection first.

| Command | Effect |
|---|---|
| `ign alarm-journal list` | All journal profiles |
| `ign alarm-journal get --name N` | One profile |
| `ign alarm-journal create --name N --datasource DB [options]` | Create a DATASOURCE-type profile |

`create` options and defaults:

| Option | Default | Meaning |
|---|---|---|
| `--min-priority` | `Diagnostic` | Lowest priority stored (`Diagnostic` logs everything); other values `Low`, `Medium`, `High`, `Critical` |
| `--description` | none | Free text |
| `--prune-age` / `--prune-units` | `90` / `DAY` | Delete events older than this (`DAY`, `WEEK`, `MONTH`, ...) |
| `--table-name` | `alarm_events` | Events table |
| `--data-table-name` | `alarm_event_data` | Associated-data table |
| `--dry-run` | off | Print the array-wrapped payload; no call |
| `--confirm` | off | Skip the POST confirmation prompt |
| `--scan/--no-scan` | scan | Post `/scan/config` afterwards |

`create` wraps the resource in a one-element JSON array because
`POST /data/api/v1/resources/ignition/alarm-journal` rejects a bare object
with `400 Not a JSON Array`. The journal registers live; the target database
gets its tables on first event. Column encodings, the indexes an analysis page
needs, and query-caching rules are in `references/alarm-journal-sql.md`.

Example:

```
ign alarm-journal create --name Demo_Journal --datasource Demo_DB --min-priority Diagnostic --confirm
```

## Agent checklist

- Before `create`/`update`: read the config file and echo it back (minus any
  password) for confirmation.
- Before `delete`: confirm the name; pass `--yes` only when the user asked to
  skip the prompt.
- Surface `Error:` and `Hint:` lines verbatim; a not-found name prints
  `Error: connection '<name>' not found.`
- Never hand-edit `config/resources/core/ignition/database-connection/**`;
  these verbs are the writer.

## References

| File | Summary |
|---|---|
| `references/connection-config-shape.md` | The 25 `ConnectionConfig` fields, a minimal SQLite file, casing rules, `backupConfig` |
| `references/jwe-refusal.md` | What the JWE guard rejects, where it fires, how to set encrypted credentials |
| `references/alarm-journal-sql.md` | `alarm_events` columns and encodings, indexes, per-dialect named queries, cache snapping, no REST read |
