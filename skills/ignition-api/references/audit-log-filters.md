# `system.util.queryAuditLog` filter behavior (8.3 database profile)

Verified against a database-backed audit profile on Ignition 8.3.

## Signature and result

```python
system.util.queryAuditLog(
    auditProfileName=..., startDate=..., endDate=...,
    actionFilter=..., actorFilter=...,
    actionTargetFilter=..., actionValueFilter=...,
)
```

Returns a Dataset with columns: `Timestamp`, `Actor`, `Actor Host`, `Action`,
`Action Target`, `Action Value`, `Result Code`, `Result`, `System`,
`Context Code`, `Context`.

## Filter gotchas

| Filter | Behavior |
|---|---|
| `actionFilter`, `actorFilter` | Exact match only. Wildcards match nothing |
| `actionTargetFilter`, `actionValueFilter` | Silently ignored by the database profile. A filter for a nonexistent target returns the full window |

Filter `Action Target` and `Action Value` client-side after the query, for
example by iterating the dataset rows and comparing the column values.

## Write visibility

`system.util.audit(..., auditProfile=...)` persists through store-and-forward.
A readback in the same script execution sees zero new rows; the entry is
visible on the next execution. Do not treat an immediate empty result as a
failed write.
