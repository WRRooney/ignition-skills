# Tag read and write permissions

Every tag, folder and UDT instance may carry `readPermissions` and `writePermissions`.
Each is a **permission set**, the same shape the gateway uses for tag-provider settings
(`readPermissions`, `writePermissions`, `editPermissions`) and for gateway security
properties (`accessPermissions`, `designerPermissions`, and so on):

```json
{
  "type": "AnyOf",
  "securityLevels": [
    {"name": "Authenticated", "children": [
      {"name": "Roles", "children": [{"name": "Operator", "children": []}]}]},
    {"name": "APIKey", "children": [{"name": "Write", "children": []}]}
  ]
}
```

- `securityLevels` is a tree that mirrors the gateway's Security Levels page. A leaf
  grants the whole path from the root, so the example grants
  `Authenticated/Roles/Operator` and `APIKey/Write`.
- `type` is `AnyOf` (an actor needs one granted path) or `AllOf` (needs every path).
- An empty `securityLevels` list grants everyone. An absent key means the tag inherits
  from its folder or UDT type, or is open.
- Tag permissions are checked **in addition to** the provider's own sets: a provider
  `writePermissions` of `Authenticated` plus a tag `writePermissions` of
  `Authenticated/Roles/Operator` means an operator who is authenticated may write.
- API tokens carry security levels under `APIKey/...`. A token that cannot pass the
  provider's `editPermissions` gets 403 from `tags/import` for that provider.

## Authoring

```python
from ignition_gen_sdk import PermissionSet, TagBuilder

tag = (
    TagBuilder().name("Setpoint").datatype("Float8").memory().value(0.0)
    .permissions(write=PermissionSet.any_of("Authenticated/Roles/Operator", "APIKey/Write"))
    .build()
)
```

`PermissionSet.any_of(*paths)` and `.all_of(*paths)` build the tree from slash paths and
merge shared prefixes. `PermissionSet.everyone()` is the explicit open set. `Tag`,
`UdtInstance` and UDT member tags accept `readPermissions` / `writePermissions`; a member's
set may also be bound to a UDT parameter (`{"bindType": "parameter", "binding": "{Perms}"}`).

On disk the block sits flat beside the other tag properties in `tags.json` / `udts.json`;
`ign tag set-udt-member-prop` and `set-udt-type-prop` can patch it as a JSON value.

## Verify

`ign api GET /data/api/v1/resources/ignition/tag-provider/find?name=<provider>` shows the
provider's three sets. For a tag, read its definition file under
`config/resources/core/ignition/tag-definition/<provider>/...` and look for the block. A
write that silently fails while the definition looks right usually means the provider's
set blocks it, not the tag's.
