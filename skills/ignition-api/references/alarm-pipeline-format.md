# Alarm pipeline `data.bin` format

Location: `projects/<name>/com.inductiveautomation.alarm-notification/alarm-pipelines/<Pipeline>/data.bin`
with a sibling `resource.json`.

Alarm pipelines have no write API:
`/data/alarm-notification/api/v1/pipeline` and `.../pipelines` are GET-only
status endpoints. Author pipelines in the Designer; use `ign alarm-pipeline`
only to read them and make text edits.

`data.bin` is gzipped with a string pool referenced by id. `replace-text`
only ever replaces a complete pool entry, which cannot change the block
graph. Never patch the bytes by hand or edit a substring of an entry.

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
