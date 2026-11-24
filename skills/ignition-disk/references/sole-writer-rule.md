# The sole-writer rule

Every file under `config/resources/**` and `projects/**` is created and
edited only by an `ign` verb, which serializes from a validated Pydantic
model. The agent never writes those paths itself.

## Shapes hand-written JSON gets wrong

The gateway often rejects these silently:

- Perspective `events` emitted as `{"events": {"onActionPerformed": {...}}}`
  instead of `{"events": {"component": {"onActionPerformed": {...}}}}`; the
  view would not open.
- View params emitted as `{"tagPath": {"value": "", "dataType": "String"}}`
  instead of `{"tagPath": "Tanks/T01"}`.
- Bindings with a constant expression where a plain prop value belongs.
- Embedded view params under `props.viewParams` (ignored) instead of
  `props.params`.

## Banned vectors

All of them, not just the editor tools:

- Write / Edit tools on those paths
- shell redirection (`>`, `>>`, `tee`), heredocs
- `sed -i`, `python -c "json.dump(...)"`
- `cp`, `mv`, `rm` into or within those paths
- one-off scripts that import the SDK's disk backends or models to route
  around a missing CLI option

The CLI is the interface: a backend class called from a scratch script skips
the CLI's validation, dry run, layer guard, JWE guard, and scan handling.
Report a missing capability to the user instead (see below).

## What `ign` enforces at its write path

- Layer guard: refuses `config/resources/local/`.
- JWE guard: refuses encrypted-credential payloads.
- Scan after write (default on).
- Manifest record for `ign diff`.

## Auto-scaffold

Write verbs create missing subdirectories under an existing project (for
example `projects/Demo/com.inductiveautomation.perspective/views/` when the
project has never had Perspective opened). They still refuse when
`projects/<name>/project.json` does not exist: create projects with
`POST /data/api/v1/projects`, not by scaffolding on disk, because a disk-only
project skips `global-props` initialization.

Read-only verbs (`ign page list`, `ign session-props` listing) never create
directories. An empty `page-config/` or `session-props/` directory is itself
a resource that shadows the parent project's, so an accidental `mkdir` on a
read path breaks routing.

## When the shape is missing

Stop that operation. Tell the user which verb or option is missing, which
commands you checked (`ign <group> --help`, the `ign api` resource path), and
what remains undone. Do not fall back to writing the file, and do not read,
edit, clone or upgrade `ignition-gen-sdk` unless the user asks for SDK work.
