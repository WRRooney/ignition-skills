# Alarm journal storage: table shape, SQL, and caching

An alarm journal profile (`ign alarm-journal create`, `profile.type: DATASOURCE`,
`queryOnly: false`) writes to `alarm_events` and `alarm_event_data` in the named
database connection. The tables are created on the first event.

## `alarm_events` columns, as stored in 8.3

| Column | Meaning |
|---|---|
| `id` | row id |
| `eventid` | text UUID shared by an alarm's active, ack, and clear rows |
| `source` | full alarm source path |
| `displaypath` | display path, the natural grouping key |
| `priority` | integer 0 Diagnostic, 1 Low, 2 Medium, 3 High, 4 Critical |
| `eventtype` | integer 0 active (raise), 1 clear, 2 acknowledge |
| `eventflags` | integer flags |
| `eventtime` | epoch milliseconds stored as text, not a datetime string |

Wrong: creating the journal with the default `minPriority` and then wondering
why diagnostic-priority alarms never appear; parsing `eventtime` as a timestamp
string. Right: `--min-priority Diagnostic` (the `ign` default) and
`int(eventtime)`.

From this table: alarm rate per window (`eventtype = 0` grouped by time
bucket), top-N and chattering alarms (group by `displaypath`), time to
acknowledge and time in alarm (join active to ack or clear rows on `eventid`),
priority distribution, flood windows.

## Schema and indexes

- The primary key is `(id, eventtime)`, so range predicates on `eventtime`
  alone cannot use it. Add explicit indexes on `(eventtime)` and `(eventid)`
  before building analysis pages over the journal.
- The journal profile reads the same datasource as named queries, so a "fall
  back to `system.alarm.queryJournal`" path cannot cover a database outage; it
  only hides broken SQL behind an unbounded scan. Fail loudly and surface the
  error on the page instead.

## Dialects

Keep one full named-query set per dialect (`Alarm/MySQL/<name>`,
`Alarm/PostgreSQL/<name>`) and pick at runtime by sniffing the vendor name
from `system.db.getConnectionInfo`, memoized in `system.util.getGlobals()` with
an override constant for testing. Escape `LIKE` wildcards when a tag path
becomes a filter and strip the provider prefix.

## Named query caching

Enable caching and snap the range end down to the poll quantum so every
session sends identical parameters; otherwise the gateway cache never hits. One
`getAnalysis(hours, pathFilter)` call that returns the whole page (counts, bad
actors, trends) is cheaper than five bindings. In the named-query resource,
`sqlType` in the parameter list is the Ignition `DataType` ordinal, and a
`:name` inside a SQL comment counts as a parameter use (`ign named-query write`
refuses the mismatch the same way the gateway does).

## No REST read

There is no REST endpoint for alarm status or journal events;
`system.alarm.queryJournal` and `queryStatus` are scripting-only. For live
counts prefer the Alarm Metrics tag properties (ignition-tag skill). A SQLite
journal file can be read directly for headless verification.

## Verify

`SELECT eventtype, COUNT(*) FROM alarm_events GROUP BY eventtype` minutes after
creating a self-firing alarm tag (ignition-tag skill, `alarm-test-bed`); all
three event types should appear. Confirm the profile with
`ign alarm-journal list`.
