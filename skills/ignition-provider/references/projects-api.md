# Project records through the API (pointer)

Project CRUD lives at `/data/api/v1/projects` and is not wrapped by an `ign`
verb; use `ign api`. The canonical rules and recovery steps live in the
ignition-api skill:
[`put-projects-full-replace.md`](../../ignition-api/references/put-projects-full-replace.md).

In short: `PUT /projects/{name}` is a full replace, so read the record first
and PUT the complete object (a partial body has blanked `title`, flipped
`inheritable` to `false`, and emptied a child's `parent`); create projects with
`POST /projects` carrying `defaultDb` and `tagProvider`, never by scaffolding
`project.json`; a damaged record is fastest restored from git plus
`/scan/projects`.
