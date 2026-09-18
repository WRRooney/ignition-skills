# UDT instance override rules

Three behaviors of Ignition 8.3 instance overrides that fail silently: the file imports, the config scan reports clean, and the only symptom is bad quality on a member or an alarm that is active when it should not be.

## 1. An override leaf must state `valueSource` explicitly

Even when the type already declares the member as `memory`, an instance override of that member that omits `valueSource` reads bad quality. This cascades: a bad `Setpoint` takes down any expression member that references it, so a derived `Active` bit never evaluates and the alarm on it never fires.

```json
{"name": "Pump01", "tagType": "UdtInstance", "typeId": "Pump",
 "tags": [{"name": "Speed", "tagType": "AtomicTag", "valueSource": "memory", "value": 1200.0}]}
```

Instance overrides write every nested node as `tagType: "AtomicTag"` regardless of what the member is in the type; that is the Designer convention and the models accept it.

## 2. An `alarms` override replaces the alarm; omitted keys take Ignition defaults

An override carrying only `{"name": "Overspeed", "priority": "Critical"}` does not inherit the type's `mode` and `setpointA`. It becomes the default alarm: `Equality` (or, if `mode` was inherited from nothing, an inclusive `AboveValue` against `setpointA` 0.0), which is `0 >= 0` and active forever.

Restate the full trigger on every alarm override: `mode`, `setpointA` (and `setpointB` for range modes), `inclusiveA`.

```json
{"name": "Speed", "tagType": "AtomicTag", "valueSource": "memory", "value": 0.0,
 "alarms": [{"name": "Overspeed", "priority": "Critical", "mode": "AboveValue",
             "setpointA": 2000.0, "inclusiveA": true}]}
```

## 3. An undriven alarm bit counts as active

An alarm sub-instance enabled at the type level whose `Active` bit is an OPC member with no item path sits at bad quality, and the gateway counts it as an active alarm. Drive every declared alarm bit; for simulation or scaffolding, drive most of them to a hard `false`.

## The diagnostic that exposes 2 and 3

Read `<folder>/Alarm Metrics.ActiveUnackCount` for the folder holding the instances (see `alarm-metrics.md`). When it equals the number of alarms configured beneath the folder, every alarm is active, which means defaults or undriven bits, not real conditions.

## Verifying

`GET /tags/export` returns configuration only, never runtime quality, so none of these can be confirmed headlessly through the API. Confirmation needs a live session: a scratch Perspective view rendered with `ign view validate` (needs the `[runtime]` extra) or the Designer's tag browser. Remove scratch views once the check is done.
