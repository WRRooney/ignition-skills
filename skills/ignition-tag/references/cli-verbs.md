# `ign tag` verbs

| Intent | Command |
|---|---|
| Preview or validate tag JSON, no gateway | `ign tag build [--file F]` |
| Push atomic tags | `ign tag push --provider P --path X [--file F] [--backend auto\|api\|disk] [--collision-policy ...] [--dry-run] [--no-scan]` |
| POST an arbitrary `tags/import` body (multi-tag, instances, value writes) | `ign tag import --file F --provider P [--path X] [--collision-policy ...] [--type json] [--dry-run] [--confirm] [--no-scan]` |
| Author a UDT type definition (disk only) | `ign tag udt-type --file F --provider P --path X [--dry-run] [--no-scan]` |
| Author UDT instances on disk (replaces the folder's `udts.json`) | `ign tag udt-instance --file F --provider P --path X [--dry-run] [--no-scan]` |
| Patch one property on members of an existing type file | `ign tag set-udt-member-prop --prop K --value V --provider P --path X [--where K=V] [--dry-run] [--no-scan]` |
| Patch one property on the type node itself | `ign tag set-udt-type-prop --type NAME --prop K --value V --provider P --path X [--dry-run] [--no-scan]` |
| Delete a tag, folder or instance directory | `ign tag delete --provider P --path X [--kind instance\|type] [--name PATTERN]... [--dry-run] [--no-scan]` |

Every option above exists in `--help`; do not invent others. `--provider` defaults to `default` (or `IGNITION_TAG_PROVIDER`). Append `--dry-run` first on anything that writes. Surface `ign`'s stdout and any `Error:` / `Hint:` stderr lines verbatim.

Without `--file`, `build` and `push` operate on a built-in demo OPC tag named `SmokeTestLevel`; that is a smoke test, not an authoring path.
