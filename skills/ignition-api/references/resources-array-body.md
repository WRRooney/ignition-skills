# Resources API: array body, element shape, live registration

`POST` and `PUT /data/api/v1/resources/ignition/<type>` (the "Modify ...
(multiple)" family: `alarm-journal`, `database-connection`, `tag-provider`,
and the rest) expect the request body to be a JSON **array** of resource
objects, even for a single resource. A bare object returns:

```
400 Unable to parse body: Not a JSON Array: {...}
```

## Element shape

Verified for `alarm-journal`; other types follow the same envelope with a
type-specific `config`:

```json
[
  {
    "name": "Demo_Journal",
    "collection": "core",
    "enabled": true,
    "description": "",
    "config": {
      "profile": { "type": "DATASOURCE", "queryOnly": false },
      "settings": { "datasource": "Demo_DB", "minPriority": "Diagnostic" }
    }
  }
]
```

Get the settings schema and defaults from the type description:

```
ign api GET /data/api/v1/resources/type/ignition/<type>
```

Look under `extensionPoints[].addComponent.settingsSchema.properties`.

Append `?allowInvalidReferences=true` when the body references a resource the
gateway has not validated yet (for example a datasource created moments
earlier).

## Live registration

Config resources created or modified through the resources API register
immediately: a new database connection opens, and an alarm journal starts
storing events without a scan or restart. This is distinct from project
resources written to `projects/**`, which the gateway notices only after
`POST /data/api/v1/scan/projects`; a project resource that still does not
show after a scan is malformed or has a runtime error in `ign logs`, never
waiting on a reload (see the ignition-disk skill).

`ign alarm-journal create`, `ign db-conn create`, and `ign provider create`
build the array envelope for you. Use raw `ign api` for resource types that
have no dedicated verb yet.

## Signatures

`GET /data/api/v1/resources/find/ignition/<type>/<name>` returns the resource
including an opaque `signature`. Modify and delete must send that signature
back in the element; a stale or empty one is rejected. `ign provider update`,
`ign db-conn update` and their `delete` verbs fetch it for you (two calls);
`delete-bulk` needs a file of `{name, signature}` pairs collected with `get`.

## Which read paths answer

| Request | Result |
|---|---|
| `GET /resources/ignition/<type>` | 405 for several types (`tag-provider`); the collection is POST/PUT only |
| `GET /resources/names/ignition/<type>` | `{"items": [{"name", "enabled", "modes"}], "metadata": {...}}` |
| `GET /resources/find/ignition/<type>/<name>` | one resource with its `signature` |
| `GET /resources/type/ignition/<type>` | settings schema and defaults |
| `GET /resources/ignition/tag-type-definition/...` | rejected; UDT types have no per-resource read (use `/tags/export?includeUdts=true`) |
| `/tags/read`, `/tags/browse`, `/tags/write` | do not exist; only `/tags/export` and `/tags/import` |
| views, style classes, scripts | no endpoint at all; verify by disk shape and a clean `/scan/projects` |

Enumerate with `names`, read config with `find`, read tag structure with
`/tags/export` (configuration only, never live values), and observe a live
value with a scratch Perspective view. The OpenAPI document the gateway serves
is authoritative for which paths exist; `ign api` pre-validates against it, so
a guessed endpoint is an exit-1 `Path error` before any request is sent.
