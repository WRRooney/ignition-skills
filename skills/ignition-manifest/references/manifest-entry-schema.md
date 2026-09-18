# Manifest entry schema

Path: `<state-dir>/manifest/<resource-type>.json` (default `./.ign/manifest/`).
Each file is one JSON object keyed by resource id.

```json
{
  "<resource-id>": {
    "payload": {} ,
    "sha256": "<64-hex>",
    "timestamp": "<iso8601, UTC>",
    "backend": "api" | "disk"
  }
}
```

| Field | Meaning |
|---|---|
| `payload` | The JSON that was sent or written, in the shape of the live artifact: the API request envelope for the `api` backend, or the bare on-disk shape (a list for a tags file) for the `disk` backend |
| `sha256` | `sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))` |
| `timestamp` | Time of the record, UTC, ISO 8601 |
| `backend` | Which backend performed the write |

## Resource id conventions

| Type | Id | Example |
|---|---|---|
| `tags` | `<provider>/<tag path>` | `default/Tanks/T01` |
| `views` | `<project>/<view path>` | `Demo/Main/Overview` |
| `providers` | `<provider name>` | `default` |
| `database-connections` | `<connection name>` | `Demo_DB` |

## Canonical hashing

The stored hash is over the canonical form: keys sorted, no whitespace.
`json.dumps(..., sort_keys=True)` alone still inserts spaces after `:` and
`,`, and those spaces change the hash, so `separators=(",", ":")` is
required.

The artifact on disk is written with `indent=2`. Its bytes never hash to the
manifest value even when it is semantically identical. To verify by hand:

```python
import hashlib, json
payload = json.load(open("view.json"))
print(hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
```

`ign diff` does this for you: it parses `--current-file`, re-canonicalizes,
and compares.

## Write semantics

- Entries are recorded only after a successful push or write, never on a
  dry run.
- Writes are atomic: a `.tmp` file is written and renamed over the manifest.
- A manifest that fails to parse is treated as empty and rebuilt on the next
  record; nothing is repaired in place.
- A `delete` records an empty `{}` payload as a tombstone so a later diff of
  the deleted resource returns exit 1 rather than exit 2.
