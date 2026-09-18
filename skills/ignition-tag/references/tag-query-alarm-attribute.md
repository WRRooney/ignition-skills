# `system.tag.query` attribute filter

`system.tag.query` accepts an `attributes` condition that filters to tags carrying a given feature. The wire values come from the gateway's `CommonTagAttributes` enum:

| Enum | Wire value |
|---|---|
| `Alarms` | `alarm` |
| `AlarmMetrics` | `alarm-metrics` |
| `Disabled` | `disabled` |
| `History` | `history` |
| `Inherited` | `udt-inheritance` |
| `Override` | `override` |
| `Scaling` | `scaling` |
| `Scripting` | `scripting` |
| `Security` | `security` |

## Finding every alarm-bearing tag in a provider

```python
results = system.tag.query("default", {
    "condition": {
        "path": "*",
        "attributes": {"values": ["alarm"], "requireAll": True},
    },
    "returnProperties": ["tagType", "meta_area"],
})
```

The `*` path wildcard is recursive, so one call per provider covers the whole tree.

## What comes back

Each result is the atomic tag that holds the alarm configuration, not the UDT instance around it. To learn something about the enclosing instance, put a `meta_*` custom property on the alarm-bearing member in the type and list it in `returnProperties`; the value comes back with the tag, and comes back `null` for a tag that has no such property. That null is a useful signal for "alarm configured outside the standard types".

## What does not work

`TagSearchFilter` declares `_alarms_`, `_tagpermissions_` and `_tageventscripts_` search fields, but those belong to the Designer's tag report tool, not to `system.tag.query`. The query's own condition fields are only `path`, `tagType`, `valueSource`, `quality`, `hierarchy`, `properties`, `attributes` and node id. Passing an alarm sub-condition to `system.tag.query` fails.
