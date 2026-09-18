# UDT scan merge semantics

What `POST /scan/config` does with a changed `tag-type-definition/**/udts.json`, and how to work around the part it does not do.

## Additions merge, kind changes are refused silently

The config scan merges new members into an already-loaded UDT type. It silently refuses a member kind change, for example turning an `AtomicTag` member into a `UdtInstance` member (or the reverse). The on-disk file shows the new shape, the gateway keeps running the old one, and nothing is logged.

To change a member's kind:

```bash
ign tag delete --provider default --path Equipment --kind type      # removes the type dir, scans
ign tag udt-type --provider default --path Equipment --file pump.json   # rewrites, scans
# recreate instances that depended on the type
ign tag import --file instances.json --provider default --path Area1
```

Then round-trip: export the type with `ign api GET "/data/api/v1/tags/export?provider=default&path=_types_%2FEquipment&recursive=true&includeUdts=true"` and diff it against the file.

## Whole-file writes drop siblings

`udt-type --file` replaces the folder's `udts.json` with the file's content. A file listing one type in a folder that held five leaves one. Every consumer of the four missing types breaks with no error at write time.

- For one property on members: `ign tag set-udt-member-prop`.
- For one property on the type node: `ign tag set-udt-type-prop`.
- For adding a type to a family file: include every existing sibling in the file, and diff the list of type names before and after the write.

## Provider permission gate

`/tags/import` is checked against the provider's `editPermissions`. A provider requiring the `Authenticated` security level rejects token-authenticated imports (`Insufficient Tag Provider Edit Permissions`). Disk writes plus `/scan/config` are not permission-checked, so `udt-type`, `udt-instance` and `tag push --backend disk` remain available for that provider. Inspect with `ign provider get <name>` and look at `config.settings.editPermissions`.

## Scan lock

Disk-writing tag verbs acquire the gateway's config scan lock before writing and release it with the scan, so the gateway does not read a half-written file and apply its own collision policy. A failed lock is a `WARNING:` on stderr; the write still happens.
