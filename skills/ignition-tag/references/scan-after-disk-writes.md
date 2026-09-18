# Scan after disk writes (pointer)

The gateway does not watch its data directory; after any file change under
`config/resources/**` a `POST /data/api/v1/scan/config` tells it to reload
(`/scan/projects` for `projects/**`). Endpoints, response shape, the config
scan lock, and what a scan does and does not reload are canonical in the
ignition-disk skill:
[`scan-endpoints.md`](../../ignition-disk/references/scan-endpoints.md).

Tag-verb specifics:

- Every disk-writing tag verb (`push --backend disk`, `udt-type`,
  `udt-instance`, `set-udt-member-prop`, `set-udt-type-prop`, `delete`) scans
  by default and takes the config scan lock first. `tag import` scans too, even
  though the import registers live, so disk and gateway agree.
- Success output for disk verbs is `Written to disk: <path>` with no separate
  scan line; a failed scan or lock prints `WARNING:` on stderr and the command
  still exits 0 because the file is already on disk.
- `--no-scan` is for offline work only; say a scan is owed and run
  `ign api POST /data/api/v1/scan/config --confirm` later.
