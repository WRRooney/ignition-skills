# The sole-writer rule

Every file under `config/resources/**` and `projects/**` is created and
edited only by an `ign` verb, which serializes from a validated Pydantic
model. The agent never writes those paths itself.

## Why

Hand-written or passed-through JSON hallucinates shapes the gateway silently
rejects. Verified examples:

- Perspective `events` emitted as `{"events": {"onActionPerformed": {...}}}`
  instead of `{"events": {"component": {"onActionPerformed": {...}}}}`; the
  view would not open.
- View params emitted as `{"tagPath": {"value": "", "dataType": "String"}}`
  instead of `{"tagPath": "Tanks/T01"}`.
- Bindings with a constant expression where a plain prop value belongs.
- Embedded view params under `props.viewParams` (ignored) instead of
  `props.params`.

A model with a fixture test fixes the shape once for every future write. A
hand edit fixes one file and leaves the bug for the next.

## Banned vectors

All of them, not just the editor tools:

- Write / Edit tools on those paths
- shell redirection (`>`, `>>`, `tee`), heredocs
- `sed -i`, `python -c "json.dump(...)"`
- `cp`, `mv`, `rm` into or within those paths
- one-off scripts that import the SDK's disk backends or models to route
  around a missing CLI option

That last one matters: the CLI is the interface. Calling a backend class from
a scratch script skips the CLI's validation, dry run, layer guard, JWE guard,
and scan handling, and leaves the gap in place. A missing capability is a CLI
bug: add the option with a test, then run the CLI.

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

Stop. Add or fix the Pydantic model in the SDK with a fixture test, add the
CLI option, then emit through `ign`. Do not fall back to writing the file.
