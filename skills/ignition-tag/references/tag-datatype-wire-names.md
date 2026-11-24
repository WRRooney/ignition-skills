# Tag data type wire names and value echoes

Tag JSON uses Ignition's own type names. The SDK's `Tag.dataType` literals are
the wire names.

| Wire `dataType` | Meaning | Common mislabel |
|---|---|---|
| `Float8` | 64-bit double | `Double` |
| `Float4` | 32-bit float | `Float` |
| `Int4` | 32-bit int | `Integer` (accepted alias) |
| `Int8` | 64-bit long | `Long` |
| `Int1`, `Int2` | byte, short | |
| `Boolean`, `String`, `DateTime`, `Document`, `DataSet` | as named | |
| `Int4Array`, `Float8Array`, `StringArray`, ... | array types | |

Never write a label (`"dataType": "Double"`). Do not default to `Float8`; most
analog process values are `Float4`.

UDT *parameters* use a different, smaller set (`String`, `Float`, `Integer`,
`Boolean`, ...); do not mix the two sets.

## Value echoes

A memory tag pushed with `"value": 42.0` comes back from `/tags/export` with
both `value` and `defaultValue: 42.0`; either serves as the initial value.
Set `enabled: true` explicitly on atomic tags.

## Verify

Push one tag of each type with `ign tag push` and diff
`ign api GET '/data/api/v1/tags/export?provider=default&path=<folder>&recursive=true&type=json'`
against the body you sent.
