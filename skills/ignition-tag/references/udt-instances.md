# UDT instances

```json
[{"name": "Pump01", "tagType": "UdtInstance", "typeId": "Pump",
  "parameters": {"DeviceRoot": {"dataType": "String", "value": "Area1/Pump01"}}}]
```

Two write paths:

- `ign tag import --file instances.json --provider default --path Area1` posts through `/tags/import` (merge-capable, registers live). `--dry-run` also resolves each `typeId` against the on-disk type definitions when the data dir is visible and lists issues.
- `ign tag udt-instance --file instances.json --provider default --path Area1` writes `tag-definition/default/Area1/udts.json` on disk. It replaces the folder's instance list, so include every instance the folder should end up with.

`tag push` rejects `UdtInstance` nodes unless `--backend api`, because the disk path writes `tags.json`, which is the wrong file for instances.

Instance overrides fail silently in three ways (bad quality or phantom alarms, never an error): an override leaf must restate `valueSource`; an `alarms` override replaces the whole alarm and omitted keys take Ignition defaults, not the type's; an undriven alarm bit counts as active. Full rules in `udt-instance-overrides.md`.
