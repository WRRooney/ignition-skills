# `PUT /data/api/v1/projects/{name}` is a full replace

"Modify Project" replaces the entire project record. Any field omitted from
the body is reset to its default, not left alone.

A body of `{"enabled": true}` sent to an inheritable parent project rewrote
its `project.json` with the title and description blanked and
`inheritable: true` flipped to `false`. Sent to a child project, the same
pattern cleared `parent`, so the child silently stopped inheriting every
view, script, and page from its template. Nothing errored; the breakage was
noticed only when inherited resources vanished at runtime.

## Safe procedure

1. Read the current record: `ign api GET /data/api/v1/projects/<name>` (or
   read `projects/<name>/project.json` on disk).
2. Modify only the field you need in that complete object.
3. `PUT` the complete object back.

Fields in the record: `name`, `title`, `description`, `enabled`, `parent`,
`inheritable`, `defaultDb`, `tagProvider`, `userSource`, `identityProvider`.
On disk, `projects/<name>/project.json` holds the first five:

```json
{ "title": "Demo", "description": "", "enabled": true, "inheritable": false, "parent": "Global" }
```

If a project record is damaged and the data directory is under version
control, restoring `projects/<name>/project.json` from git and rescanning is
faster than reconstructing it.

## It is not a reload trigger

`PUT /projects` does not recompile project library scripts and does not
reload Perspective resources. Use `POST /data/api/v1/scan/projects` for that.

## Creating projects

Create a project with `POST /data/api/v1/projects`, never by scaffolding
`project.json` on disk:

```bash
ign api POST /data/api/v1/projects --confirm --json '{
  "name": "Demo", "title": "Demo", "description": "", "enabled": true,
  "parent": "", "inheritable": false,
  "defaultDb": "Plant", "tagProvider": "default",
  "userSource": "", "identityProvider": ""}'
```

A disk-only project skips the gateway's `ignition/global-props` initialization
(a gzipped binary `data.bin` that cannot be hand-built). Any later PUT that
touches the collection-stored fields (`defaultDb`, `tagProvider`, `userSource`,
`identityProvider`) fails with:

```
MODIFY illegal, 'ResourceId{resourcePath=ignition/global-props, collectionName=<name>}' doesn't exist
```

Set `defaultDb` and `tagProvider` in the create call rather than
create-then-PUT. If a project was already disk-scaffolded and shows this
error, `DELETE /data/api/v1/projects/<name>?confirm=true` and POST it again.

## What the SDK's project verbs assume

`ign view write`, `ign page mount`, `ign script write` and the other project
writers require `projects/<name>/project.json` to exist and create missing
subdirectories under it. They never create the project, and `project.json`
has no SDK writer.
