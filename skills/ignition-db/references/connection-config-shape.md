# `ConnectionConfig` file shape

The file passed to `ign db-conn create/update --config-file` is the inner
`config` object of a database-connection resource, exactly as
`ign db-conn get <name>` prints it. Any subset is accepted; the gateway fills
the rest with defaults. Unknown keys are rejected (`extra="forbid"`).

## Minimal SQLite example

```json
{
  "driver": "SQLite",
  "translator": "SQLITE",
  "connectURL": "jdbc:sqlite:${data}/Demo_DB.db",
  "username": "",
  "validationQuery": "SELECT 1"
}
```

Casing matters: `driver` is the driver's display name (`SQLite`, `MySQL`,
`PostgreSQL`), `translator` is upper case (`SQLITE`, `MYSQL`, `POSTGRES`). Get
both from `ign driver describe <name>`, which also carries `classname`,
`urlFormat`, `defaultProps`, and `defaultValidationQuery` for database types
you have no existing connection to clone. `ign db-conn describe` returns
resource-type metadata (type id, counts, metrics), not a field schema; clone
`ign db-conn get <existing>` for the real shape. The gateway creates a SQLite
file on first connect, which is a cheap liveness check.

## All 25 fields

| Field | Example | Notes |
|---|---|---|
| `driver` | `"MySQL"` | Must match `ign driver list` |
| `translator` | `"MYSQL"` | From the driver description |
| `connectURL` | `"jdbc:mysql://db:3306/demo"` | `${data}` expands to the gateway data dir |
| `username` | `"demo"` | |
| `password` | `"..."` | Plaintext only; see the JWE refusal rule |
| `connectionProps` | `"connectTimeout=120000"` | `;`-separated driver properties |
| `connectionResetParams` | `""` | |
| `validationQuery` | `"SELECT 1"` | |
| `validationSleepTime` | `10000` | ms |
| `testOnBorrow` | `true` | |
| `testOnReturn` | `false` | |
| `testWhileIdle` | `false` | |
| `poolInitSize` | `0` | |
| `poolMinIdle` | `0` | |
| `poolMaxIdle` | `8` | |
| `poolMaxActive` | `8` | |
| `poolMaxWait` | `5000` | ms |
| `evictionRate` | `-1` | |
| `evictionTests` | `3` | |
| `evictionTime` | `1800000` | ms |
| `defaultTransactionLevel` | `"DEFAULT"` | |
| `failoverMode` | `"STANDARD"` | |
| `failoverProfile` | `""` | Name of the failover connection |
| `includeSchemaInTableName` | `false` | |
| `slowQueryLogThreshold` | `60000` | ms |

## `backupConfig`

A failover configuration may sit next to `config` as an outer sibling:

```json
{
  "driver": "MySQL",
  "...": "...",
  "backupConfig": { "connectURL": "jdbc:mysql://standby:3306/demo" }
}
```

`create`/`update` lift the outer `backupConfig` into the resource envelope.
A `backupConfig` nested inside the 25 fields is an unknown key and fails
validation.

## Where it lands

`config/resources/core/ignition/database-connection/<name>/config.json` with a
sibling `resource.json`. Read it to learn a shape; never edit it by hand.

## Verify

`ign db-conn names` lists the new name; `ign db-conn get <name>` shows the
config as sent plus a `signature`. The gateway's status page shows `Valid` once
the pool connects; for SQLite the `.db` file appears under the data directory.
