# Gateway security properties: `ign security`

`ignition/security-properties` is a singleton resource whose `config` holds five permission
sets and the auth settings. The sets use the same `{type, securityLevels}` tree described in
`../../ignition-tag/references/permissions.md`.

| Key | Gates |
|---|---|
| `accessPermissions` | seeing the Home section of the gateway web UI (implied by read) |
| `readPermissions` | reading every gateway page and setting (implied by write) |
| `writePermissions` | changing gateway configuration, including the config API |
| `designerPermissions` | opening the Designer |
| `createProjectPermissions` | creating projects |

API tokens hold security levels under `APIKey/...` (`Access`, `Read`, `Write` on a fresh
gateway). A token can only do what the matching set grants it: a 403 from a resource write
means `writePermissions` does not include a level the token has.

## Verbs

```bash
ign security get                                   # full config JSON
ign security get --paths                           # permission sets as slash paths
ign security get --key writePermissions

ign security set-permissions --key writePermissions \
    --any-of Authenticated/Roles/Administrator --any-of APIKey/Write   # get, patch, put
ign security set-permissions --key designerPermissions --open --dry-run
ign security set-permissions --key readPermissions --all-of Authenticated --all-of APIKey/Read

ign security update --file security.json           # PUT a whole config (validated first)
```

`set-permissions` fetches the current config and signature, replaces one set, validates the
result, and PUTs everything back, so untouched keys survive. Exactly one of `--any-of`,
`--all-of` or `--open` is required. `--dry-run` prints the new set and the old one.

## Cautions

- Removing `APIKey/Write` (or the level the current token holds) from `writePermissions`
  locks the token out of every further config write, including undoing the change. Keep an
  administrator login available before narrowing it.
- `readPermissions` narrowing can hide the config API from the token as well; test with
  `ign api GET /data/api/v1/gateway-info` afterward.
- The gateway applies the change immediately; there is no scan step for config written through
  the API.

## Verify

`ign security get --paths` after the change. The on-disk copy is
`config/resources/core/ignition/security-properties/config.json`.
