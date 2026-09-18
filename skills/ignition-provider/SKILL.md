---
name: ignition-provider
description: |
  Use when the user wants to list, inspect, create, update, delete, bulk-delete, rename or describe an Ignition 8.3 tag provider with the `ign provider` verbs (the `/data/api/v1/resources/ignition/tag-provider` resource family), or needs the resources-API and project-API rules that provider CRUD shares (array bodies, signatures, PUT is a full replace, create projects through POST).
  Positive triggers: "tag provider", "list providers", "provider names", "create provider", "delete provider", "rename provider", "describe provider", "provider config", "editPermissions", "STANDARD provider", "create a project", "PUT /projects".
  Do not trigger for: OAuth or identity providers, database providers or connections (use ignition-db), DNS or cloud providers, tags inside a provider (use ignition-tag).
---

## Verb map

Nine verbs. Four read, five mutate. Provider resources have no on-disk writer in the SDK; every verb uses the gateway API.

| Intent | Command |
|---|---|
| Full config of every provider | `ign provider list` |
| Just the names | `ign provider names` |
| One provider's config (includes its `signature`) | `ign provider get NAME` |
| Resource type schema, extension points, per-type defaults | `ign provider describe` |
| Create | `ign provider create --name N --config-file F [--dry-run] [--no-scan]` |
| Update | `ign provider update --name N --config-file F [--dry-run] [--no-scan]` |
| Delete (prompts unless `--yes`) | `ign provider delete --name N [--yes] [--no-scan]` |
| Bulk delete | `ign provider delete-bulk --entries-file F` |
| Rename (updates cross-resource references) | `ign provider rename --name N --new-name M` |

`--config-file` and `--entries-file` accept `-` for stdin. No other options exist; do not invent a `--type` shortcut. Surface `ign` output verbatim, including `Error:` and `Hint:` lines. A missing provider on `get`, `update` or `delete` reports `Error: provider 'NAME' not found.`

## Read-only start

```bash
ign provider names
ign provider get default
ign provider describe
```

`describe` returns the tag-provider resource type: its extension points (one per provider type, `STANDARD`, remote and so on), each with a settings schema and `defaultSettings`. Read it before composing a config file for an unfamiliar type.

## Config file shape (STANDARD provider)

`create` and `update` take a JSON file containing the provider's `config` object. Minimal STANDARD provider, verified against a live gateway:

```json
{
  "profile": {"type": "STANDARD", "allowBackfill": false, "enableTagReferenceStore": true},
  "settings": {
    "defaultDatasourceName": null,
    "readPermissions": {"type": "AllOf", "securityLevels": []},
    "readOnly": false,
    "writePermissions": {"type": "AllOf", "securityLevels": []},
    "editPermissions": {"type": "AllOf", "securityLevels": []},
    "valuePersistence": "Configuration"
  }
}
```

- `valuePersistence` accepts `"Configuration"` or `"Database"`; the gateway's STANDARD default is `"Database"`. Pick per intent.
- To clone an existing provider, take the `config` object from `ign provider get NAME` and edit it.
- `editPermissions` matters to the tag skills: a provider whose edit permissions require the `Authenticated` security level rejects token-authenticated `/tags/import` calls with `Insufficient Tag Provider Edit Permissions`. Empty `AllOf` lists accept the API token. Record each provider's gate in `.agents/skills/ignition-local/`.

```bash
ign provider create --name Plant --config-file plant.json --dry-run    # prints the payload
ign provider create --name Plant --config-file plant.json
```

## How the mutations work

- `create` wraps the config into the resources-API element shape (`name`, `enabled`, optional `description`, `config`) inside a JSON array. The array wrapper is a requirement of every `resources/ignition/<type>` POST and PUT; a bare object is a 400. Details in `references/resources-api.md`.
- The read and mutate verbs use a typed client generated from the gateway's OpenAPI spec. The first typed verb fetches the spec to `.ign/openapi.json` and generates the client on its own (a few seconds, with a one-time "Generating API client" message on stderr); no prior `ign openapi fetch` is needed, and the generator ships as a core dependency. `ign openapi fetch` only refreshes the spec after a gateway upgrade.
- `update` and `delete` first call `get` to fetch the current `signature`, then send it with the change. The signature is an optimistic-concurrency token; a stale one is rejected.
- `delete-bulk` takes a file holding a list of `{"name": ..., "signature": ...}` objects, so collect signatures with `get` first.
- `create`, `update` and `delete` record a manifest entry (for `ign diff`) and then POST `/data/api/v1/scan/config`. A failed scan prints `WARNING:` on stderr and exits 0, because the mutation already landed. `delete-bulk` and `rename` neither scan nor record a manifest entry.
- Resources created through the resources API register live; the scan only reconciles disk state.

## Output shapes

- `names`: `{"items": [{"name", "enabled", "modes"}], "metadata": {...}}`.
- `get`: one flat resource dict with `name`, `enabled`, `description`, `config` and the opaque `signature`.
- `list`: every provider in the `get` shape.
- `create`, `update`, `delete`: `{"success", "changes": [{"name", "type", "collection", "newSignature"}], "problem"}`. A non-null `problem` with `success: true` still means the change landed; print it.
- `--dry-run` on `create` and `update` prints the exact array body that would be posted, so the user can review it before anything is sent.

## Verify after a mutation

```bash
ign provider names                   # the new or renamed name appears, the deleted one is gone
ign provider get Plant               # config matches what was sent; note the new signature
ign diff                             # compares the last-pushed payload against the manifest entry
```

A provider that was created disabled (`"enabled": false` in the element) shows in `names` with `enabled: false` and its tags are not browsable until it is enabled through `update`.

## Confirm before mutating

- Before `create` or `update`: read the config file and echo its substance back to the user (provider type, permissions, persistence) before running.
- Before `delete`: ask the user to confirm the exact name. Pass `--yes` only when the user has explicitly said to skip the prompt, or when stdin is not a terminal and they have already confirmed.
- Before `rename`: confirm both the current and the new name. Rename updates references from other resources, so it is a gateway-wide change.

## Projects share these rules

Project CRUD (`/data/api/v1/projects`) is not wrapped by an `ign` verb yet; it goes through `ign api`. It shares the resources-API discipline and adds two traps: `PUT /projects/{name}` is a full replace that resets omitted fields (it has silently flipped `inheritable` to `false` and blanked `parent`), and a project must be created with `POST /projects`, never by scaffolding `project.json` on disk. See `references/projects-api.md` before touching a project record.

## Falling back

If a provider operation is not in the verb table, check `.ign/api_reference/` for the endpoint and use `ign api`. Do not call the gateway with any other HTTP client.

## References

| File | Summary |
|---|---|
| `references/resources-api.md` | Pointer: array body, element shape, signatures, live registration; canonical text is in the ignition-api skill |
| `references/projects-api.md` | Pointer: `PUT /projects` full replace, create via `POST /projects`; canonical text is in the ignition-api skill |
