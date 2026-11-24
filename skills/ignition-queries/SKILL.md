---
name: ignition-queries
description: Use when listing, writing, or deleting Ignition named queries with `ign named-query` (query.sql + resource.json under projects/<name>/ignition/named-query/), including bind parameters, query type (Query, Update, Scalar Query), datasource, caching, and row limits. Triggers include "named query", "ign named-query", "query.sql", "runNamedQuery", "query parameters", "cache seconds". Do not use for database connections (use ignition-db), a query binding inside a Perspective view (use ignition-perspective), or ad hoc SQL against the database.
---

# Named queries with `ign named-query`

Named queries live in `projects/<name>/ignition/named-query/<query-path>/` as `query.sql` +
`resource.json`. Only `ign` writes them; never hand-edit either file. If a needed option is
missing, stop and tell the user.

```bash
ign named-query list --project Demo
ign named-query write --project Demo --query-path Reports/PumpRuntime --file /tmp/runtime.sql \
    --database PlantDB --param start:DateTime --param end:DateTime --type Query --cache-seconds 0 --dry-run
ign named-query delete --project Demo --query-path Reports/PumpRuntime
```

| Option | Meaning |
|---|---|
| `--query-path` | Slash-separated path; also the name passed to `system.db.runNamedQuery` and query bindings |
| `--database` | Datasource name (`ign db-conn list` shows them) |
| `--param name:DataType` | Repeatable; DataType is an Ignition tag data type (`String`, `Int4`, `Float8`, `DateTime`, ...) |
| `--type` | `Query` (default), `Update`, or `Scalar Query` |
| `--cache-seconds` | Gateway-side result cache, shared across all sessions and keyed on parameter values; `0` (default) disables it |
| `--max-return-size` / `--enforce-max-return-size` | Row cap (default 100) and whether the gateway enforces it (default no) |

Rules:

- Every `:name` in the SQL must be declared with `--param`, and every `--param` must appear
  in the SQL; a mismatch fails before anything is written.
- Ignition scans SQL comments for parameters too, so keep `:word` tokens out of comments.
- Writes scan projects automatically; do not add a separate scan.
- Verify with `ign named-query list --project Demo`. A query binding in a view references the
  query by `--query-path`; see ignition-perspective `binding-discriminators.md` for the binding JSON.
