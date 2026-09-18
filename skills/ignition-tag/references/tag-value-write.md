# Writing a tag value through `/tags/import`

The Ignition 8.3 HTTP API exposes exactly two tag endpoints: `GET /data/api/v1/tags/export` and `POST /data/api/v1/tags/import`. There is no `/tags/write`, `/tags/read` or `/tags/browse`. Do not plan a verification step against `/tags/read`; `ign api` rejects it as not in the spec.

## Recipe

A minimal tag definition imported with `collisionPolicy=Overwrite` sets the value and leaves the rest of the configuration (dataType, readOnly, bindings, parent UDT structure) intact.

`body.json`:

```json
{"tags": [{"name": "Setpoint", "tagType": "AtomicTag", "value": 75.0}]}
```

```bash
ign tag import --file body.json --provider default --path Tanks/T01 --collision-policy Overwrite --confirm
```

Response: `Import complete: successCount=1 failureCount=0`. `--path` is the parent folder; the tag `name` joins it to form the full path. Verified on UDT member tags (for example self-resetting command booleans inside an instance).

Before writing inside a UDT instance, export the parent folder first (`ign api GET "/data/api/v1/tags/export?provider=default&path=Tanks%2FT01&recursive=true"`) so the structure can be restored if a fuller definition ever overwrote bindings.

## Body shape rules

- The gateway wants a `{"tags": [...]}` object; a bare top-level array is rejected with `IllegalStateException: Not a JSON Object`. `ign tag import --file` accepts a bare JSON list and wraps it in that envelope itself, but write the envelope in files you keep.
- To create several instances under a nested folder, embed the folder hierarchy in the body and omit `--path`:

  ```json
  {"tags": [{"name": "Area1", "tagType": "Folder", "tags": [
     {"name": "Pump01", "tagType": "UdtInstance", "typeId": "Pump"},
     {"name": "Pump02", "tagType": "UdtInstance", "typeId": "Pump"}]}]}
  ```

  Supplying `--path Area1` together with a folder-bearing multi-instance body makes the gateway create `Area1_duplicate_N` collision folders. Use one or the other.

## Reading

`/tags/export` returns tag structure and configuration only, never runtime value or quality. Existence in the export is the best headless proxy for "the tag landed"; whether a member resolves with Good quality can only be confirmed in a live session (Designer, or a scratch Perspective view rendered with `ign view validate`).

## Provider permission gate

`/tags/import` is checked against the target provider's `editPermissions`. A provider requiring the `Authenticated` security level fails every import, value write or instance create alike, with:

```json
{"quality": "Bad", "qualitySubCode": 514, "diagnosticMessage": "Insufficient Tag Provider Edit Permissions"}
```

For that provider use the disk verbs (`tag udt-type`, `tag udt-instance`, `tag push --backend disk`, `tag delete`) plus the automatic `/scan/config`; disk writes are not permission-checked. Value writes there need an authenticated session. Providers with empty `AllOf` permission sets accept the import path.

## Cleaning up litter

`ign tag delete --provider default --path Area1_duplicate_1` removes a collision folder's definition directory and scans. For untracked litter in a git-managed data dir, `git clean -fd <path>` followed by `ign api POST /data/api/v1/scan/config --confirm` also works.
