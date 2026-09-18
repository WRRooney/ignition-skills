# Alarm pipeline `data.bin` format

Location: `projects/<name>/com.inductiveautomation.alarm-notification/alarm-pipelines/<Pipeline>/data.bin`
with a sibling `resource.json`.

Alarm pipelines are the one gateway resource with no write API.
`/data/alarm-notification/api/v1/pipeline` and `.../pipelines` are GET-only
status endpoints. The Designer is the only authoring tool; `ign alarm-pipeline`
round-trips the binary byte-exact for reading and surgical text edits.

## Layout

```
gzip(
  [16B magic][u32 version][u64 epoch-ms][20 zero bytes]
  [u32 stringCount][ (u32 id, u24 len, utf8 bytes) * count ]
  [node stream]
)
```

Node stream: `op = (type << 3) | flags`.

| type | Meaning |
|---|---|
| 0 | empty element |
| 1 | element with attributes |
| 2 | element with children |
| 3 | element with both |
| 4 | leaf with payload |

Flags: `0x01` back-reference by id, `0x02` second name reference, `0x04`
declares an id.

The node stream refers to strings **by id, never by offset**. Changing the
bytes of a pooled string cannot move an edge in the block graph, which is why
`replace-text` is safe and why it only ever replaces a complete pool entry
(a substring edit could corrupt an unrelated entry sharing a prefix).

## Scripts inside pipelines

Script blocks are stored with no `def` header, indented one level with tabs,
and no trailing newline. `replace-text --old-file/--new-file` strips a
trailing newline from both files so an editor-saved file matches.

## Verification

`GET /data/alarm-notification/api/v1/pipelines` lists every pipeline the
gateway loaded. A pipeline that fails to deserialize is missing from the list,
so its presence after an edit is the proof the edit was valid. Pipelines
defined in an inheritable parent project are inherited by child projects and
appear in the listing for both.
