---
name: ignition-device
description: Use when the user wants to list, inspect, create, or delete an Ignition OPC UA device connection with `ign device` (the com.inductiveautomation.opcua/device resource), especially a Programmable Device Simulator, or load, replace, or read a simulator program (instructions.csv). Triggers include "device connection", "simulator device", "SIM device", "Programmable Device Simulator", "instructions.csv", "simulator program", "load program", "ModbusTcp device", "add a PLC". Do not use for OPC tags inside a provider (use ignition-tag), database connections (use ignition-db), or tag providers (use ignition-provider).
---

# Ignition devices with `ign device`

Devices are gateway config resources (`config/resources/<layer>/com.inductiveautomation.opcua/device/<name>/`).
`ign device` writes them through the resources API, so it works without disk access.

If `ign device --help` reports `No such command 'device'`, the installed SDK is older than this
skill. Stop and tell the user (`uv tool upgrade ignition-gen-sdk`); do not build the requests by hand.

## Verbs

| Verb | What it does |
|---|---|
| `ign device list` | All device connections |
| `ign device get --name N` | One device: config, enabled, signature |
| `ign device describe` | Driver type codes and each type's settings schema |
| `ign device create --name N [--type T] [--settings-file F] [--program CSV] [--dry-run] [--confirm]` | Create a device; `--type` defaults to `ProgrammableSimulatorDevice` |
| `ign device program --name N --file CSV [--dry-run] [--confirm]` | Load or replace a simulator program |
| `ign device program-get --name N` | Print the current program CSV |
| `ign device delete --name N [--yes]` | Delete a device |

Mutating verbs scan config afterwards (`--no-scan` to skip). A `WARNING:` on stderr means the scan
failed even though the exit code is 0.

## Simulator device

```bash
ign device create --name Line1Sim --program line1.csv --dry-run   # check the payload
ign device create --name Line1Sim --program line1.csv --confirm
ign device program-get --name Line1Sim                            # verify the program loaded
```

Default settings for `ProgrammableSimulatorDevice` are
`{"legacyMode": false, "repeat": true, "timeIntervalRate": 1000}`. Pass `--settings-file` to change
them. `repeat` restarts the program after the last time interval; `timeIntervalRate` is the length
in milliseconds of one Time Interval unit.

## Program CSV format

The header must be exactly these four columns. `ign` rejects anything else before calling the gateway.

```csv
Time Interval, Browse Path, Value Source, Data Type
"0","Line1/Flow","0.0","Double"
"0","Line1/Running","false","Boolean"
"0","Line1/Level","ramp(0.0, 100.0, 60.0, true)","Double"
"10","Line1/Flow","random(98.0, 100.5, true)","Double"
```

- **Time Interval**: when the row takes effect, in `timeIntervalRate` units from program start.
  Rows with `0` set initial values.
- **Browse Path**: the OPC item path under the device; folders separate with `/`.
- **Value Source**: a constant, or a function such as `ramp(...)` or `random(...)` as seen in
  programs exported from the gateway. Copy the argument order from an existing program
  (`program-get`) rather than guessing.
- **Data Type**: `Boolean`, `Int16`, `Int32`, `Int64`, `Float`, `Double`, `String`.

`program` replaces the whole program; there is no row-level edit. To change one row, run
`program-get` to a local file, edit that file, and load it back.

## Other device types

Run `ign device describe` and read the schema for the type (for example `ModbusTcp`), write the
settings object to a file, then `ign device create --name N --type ModbusTcp --settings-file s.json --dry-run`.
Connection passwords and other encrypted fields are set in the Gateway web UI, never by tooling.

## Verify

1. `ign device get --name N` shows the device with `enabled: true`.
2. Device status (Connected, Faulted) is visible in the gateway web UI under Connections > Devices.
   Tags pointing at `ns=1;s=[N]Line1/Flow` read the simulated values once the program runs.
