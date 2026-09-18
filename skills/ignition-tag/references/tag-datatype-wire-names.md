# Tag data type wire names and value echoes

Tag JSON uses Ignition's own type names, which differ from the labels a typed
model tends to use. The SDK's `Tag.dataType` literals are the wire names.

| Wire `dataType` | Meaning | Common mislabel |
|---|---|---|
| `Float8` | 64-bit double | `Double` |
| `Float4` | 32-bit float | `Float` |
| `Int4` | 32-bit int | `Integer` (accepted alias) |
| `Int8` | 64-bit long | `Long` |
| `Int1`, `Int2` | byte, short | |
| `Boolean`, `String`, `DateTime`, `Document`, `DataSet` | as named | |
| `Int4Array`, `Float8Array`, `StringArray`, ... | array types | |

Wrong: serializing an enum by its label (`"dataType": "Double"`), or using
`Float8` everywhere because the examples did; most analog process values are
`Float4`.

UDT *parameters* use a different, smaller set (`String`, `Float`, `Integer`,
`Boolean`, ...); do not mix the two sets.

## Value echoes

A memory tag pushed with `"value": 42.0` comes back from `/tags/export` with
both `value` and `defaultValue: 42.0`; either serves as the initial value.
`enabled: true` should be explicit on atomic tags; the SDK serializes with
`exclude_none`, never `exclude_defaults`, so explicit defaults survive.

## Verify

Push one tag of each type with `ign tag push` and diff
`ign api GET '/data/api/v1/tags/export?provider=default&path=<folder>&recursive=true'`
against the body you sent.
