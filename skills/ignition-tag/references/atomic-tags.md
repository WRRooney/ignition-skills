# Authoring atomic tags and their alarms

Write the tag JSON to a file and pass `--file`. The file may be a single tag object, a JSON list, or a full import body. Each tag is validated through the `Tag` model before anything is sent.

```json
{"name": "Level", "tagType": "AtomicTag", "dataType": "Float8",
 "valueSource": "memory", "value": 42.0, "engUnit": "%"}
```

```bash
ign tag build --file level.json                                   # prints the tags/import body
ign tag push --provider default --path Tanks/T01 --file level.json --dry-run
ign tag push --provider default --path Tanks/T01 --file level.json
```

Rules the model enforces:

- A standalone `AtomicTag` requires both `dataType` and `valueSource`. Only UDT member tags and folders may omit them.
- `dataType` literals: `Float4` (4-byte float), `Float8` (double), `Int4`, `Boolean`, `String`, and the rest of the Ignition set (`tag-datatype-wire-names.md`).
- `valueSource`: `memory`, `opc` (with `opcServer` + `opcItemPath`), `expr` (with `expression`), `reference` (with `sourceTagPath`), `db`.
- Names are sanitized: characters outside letters, digits, `_ ()':-` are dropped, and a name not starting with a letter or underscore gets a leading underscore.
- A `UdtType` node fed to `build` or `push` is rejected; use `udt-type`.

`--backend auto` (the default) tries the API and falls back to a disk write only on a 5xx. Use `--backend api` when the data dir is not mounted. `--collision-policy` defaults to `Overwrite` (the file is the intended end state); `MergeOverwrite` keeps members the file no longer lists.

## Alarms on a tag

Add an `alarms` array. Serialized values, not Python enum names:

```json
{"name": "Level", "tagType": "AtomicTag", "dataType": "Float8", "valueSource": "memory", "value": 0.0,
 "alarms": [{"name": "HighLevel", "priority": "High", "mode": "AboveValue", "setpointA": 90.0}]}
```

- `mode`: `AboveValue`, `BelowValue`, `BetweenValues`, `OutsideValues`, `Equality`, `Inequality`, `OutOfEngRange`, `BadQuality`, `AnyChange`, `Bit`.
- `priority`: `Diagnostic`, `Low`, `Medium`, `High`, `Critical`.
- Setpoints are `setpointA` and `setpointB` (range modes), never `setpoint`.
- Defaults the model fills: `enabled: true`, `inclusiveA: true`, `ackMode: "Manual"`, `priority: "Low"`, `mode: "Equality"`, `setpointA: 0.0`. An unspecified alarm is therefore "equal to 0", which is active for most integer tags at rest. Always state `mode` and `setpointA`.

## From Python

For generated tag sets, build with `ignition_gen_sdk.TagBuilder` (`.name().datatype().opc(...)|.memory()|.expression()|.reference()|.alarm(Alarm(...))|.history(...)|.build()`) or the models in `ignition_gen_sdk.models.tags` (`Tag`, `UdtType`, `UdtInstance`, `Alarm`), write the JSON to a file, and hand it to the CLI. Generators belong in `.ign_tools/` and run through `ign tools run`.
