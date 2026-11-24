# `ign tag import` body rules

`tag import` sends the file body (after the list wrap below) to `/tags/import`. Never import UDT type definitions (a `_types_` folder) this way; use `ign tag udt-type` (`udt-change-procedure.md`).

- The documented body is the `{"tags": [...]}` object form. `--file` also accepts a bare JSON list of tags and wraps it as `{"tags": [...]}` before sending, because the gateway rejects a bare top-level array with `Not a JSON Object`.
- For multi-instance imports into a nested folder, embed the folder hierarchy in the body (`{"tags":[{"name":"Area1","tagType":"Folder","tags":[...]}]}`) and omit `--path`. Combining `--path` with a folder-bearing body makes the gateway create `<Folder>_duplicate_N` collision folders.
- Tags imported this way register live; the default `--scan` keeps disk state aligned.
- A provider whose `editPermissions` require the `Authenticated` security level rejects token imports with `Insufficient Tag Provider Edit Permissions` (`qualitySubCode` 514). Use the disk verbs plus scan for that provider; disk writes are not permission-checked. Check with `ign provider get <name>`.
