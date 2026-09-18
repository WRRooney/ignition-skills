# Alarm Metrics tag properties

Ignition 8.3 exposes aggregated alarm rollups on every folder and UDT instance (not on the provider root). They are read as tag properties with dot addressing:

```
[default]Area1/Alarm Metrics.ActiveUnackCount     good quality, returns the count
[default]Area1/Alarm Metrics/ActiveUnackCount     bad quality (slash form is wrong)
```

Property names are case-insensitive (`activeUnackCount` and `ActiveUnackCount` resolve the same).

## Properties

| Property | Meaning |
|---|---|
| `ActiveUnackCount`, `ActiveAckCount`, `ClearUnackCount`, `ShelvedCount` | counts by state |
| `HasActive`, `HasUnacknowledged` | booleans |
| `ActiveCount{Critical,High,Medium,Low,Diagnostic}` | active count per priority |
| `UnackCount{Critical,High,Medium,Low,Diagnostic}` | unacknowledged count per priority |
| `HasActiveUnacked{Critical,High,Medium,Low,Diagnostic}` | boolean per priority |
| `Highest{Active,Acked,Unacked}Priority` | priority of the highest matching alarm |
| `Highest{Active,Acked,Unacked}Name` | its name |
| `LastActiveTime` | timestamp |

There is no plain `ActiveCount`. Total active is `ActiveAckCount + ActiveUnackCount`. The priority, name and time properties return `null` when nothing is active, so drive UI logic from the numeric counts.

## Why use them

A plain indirect tag binding on a metric property updates live, costs nothing per evaluation, and works in anonymous Perspective sessions. Polling `system.alarm.queryStatus` from a script does none of those.

## Binding pattern

Take a root tag path as a view parameter and bind:

```
{rootPath}/Alarm Metrics.ActiveUnackCount
```

with the expression guard `if(isGood({value}), {value}, 0)` on the transform so a missing folder renders as zero instead of an error overlay.

## As a diagnostic

`ActiveUnackCount` for a folder equal to the number of alarms configured beneath it means every alarm is active. That is the signature of UDT instance overrides that lost their trigger (alarm override replaced with defaults) or of alarm bits with no driver. See `udt-instance-overrides.md`.
