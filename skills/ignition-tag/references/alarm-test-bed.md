# Self-firing alarm tags for testing alarm screens

Expression tags whose value is derived from the clock cross alarm setpoints on
their own, so alarm tables, journals, and KPI screens have live and historical
data with no PLC.

## The set

Six tags under `Alarms/` with `valueSource: "expr"`:

| Tag | Expression | Alarm |
|---|---|---|
| `Oscillator` | `getSecond(now(1000))` | `AboveValue` 40 High; `AboveValue` 55 Critical; `BelowValue` 10 Low |
| `Chatter` | `getSecond(now(1000)) % 2` | `AboveValue` 0 Medium (chattering) |
| `Stale` | `90` | `AboveValue` 80 Low (never clears) |
| `FlowDeviation` | `getSecond(now(1000))` | `OutsideValues` 10..50 Medium |
| `PumpFault` | `getSecond(now(1000)) > 45` | `WhenTrue` High |
| `DiagBlip` | `getSecond(now(1000)) = 0` | `WhenTrue` Diagnostic |

`now(1000)` re-evaluates every second. Give each tag a distinct display path so
top-N and grouping KPIs have something to group. Push them with
`ign tag push --file alarms.json --provider default --path Alarms`; state `mode`
and `setpointA` on every alarm (an unspecified alarm defaults to `Equality`
against 0).

The expression language has no random function; for noise, sum sines with no
common period instead.

## Verify

`SELECT displaypath, COUNT(*) FROM alarm_events WHERE eventtype = 0 GROUP BY displaypath`
after a few minutes; all six paths accrue (the journal must be created with
`--min-priority Diagnostic` for `DiagBlip` to appear; see the ignition-db
skill). The alarm status table component shows the active ones immediately, and
`Alarms/Alarm Metrics.ActiveUnackCount` (`alarm-metrics.md`) cycles.

Remove the folder with `ign tag delete --provider default --path Alarms` when
the screen work is done; a chattering alarm left running fills the journal.
