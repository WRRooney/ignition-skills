# Alarm rosters and pipelines from scripting in 8.3

The `system.alarm` scripting surface in 8.3 lets a script manage on-call
rosters and inspect pipelines, but not create pipelines or dispatch
notifications. None of it has a REST equivalent.

| Present | Absent |
|---|---|
| `system.alarm.getRosters()`, `createRoster(name, description)` | `deleteRoster` |
| `queryStatus(...)`, `queryJournal(...)` (accept `source=["*Area1/Pump01*"]` wildcard filters) | any `/alarms` REST read; the resources API only configures the journal |
| `listPipelines()`, `acknowledge`, `shelve`, `unshelve`, `cancel` | any create-pipeline call, any direct notify call |

Pipelines are authored in the Designer and stored as a binary resource
(`alarm-pipeline-format.md`); `ign alarm-pipeline` can read and text-patch
them but never authors one.

## Wrong

Designing a notification feature around a `deleteRoster` or `createPipeline`
script call, or assuming a Maker or unlicensed-notification gateway will
dispatch anything.

## Right

- Treat roster CRUD as create-or-update: an `ensureRoster` that checks
  `getRosters()` first.
- A pipeline holds no logic. Each script block is a one-line call into a
  library function, so the routing rules stay versioned and testable; keep the
  rules themselves as data (a JSON string in a memory tag or a session prop)
  that the library reads.
- Test the pure routing logic headlessly by `exec`ing the library source with
  a fake `system` module.
- For live counts, prefer the Alarm Metrics tag properties (ignition-tag skill)
  over `queryStatus` polling.

## Verify

`ign api GET /data/alarm-notification/api/v1/pipelines` proves a pipeline edit
loaded (a pipeline that fails to deserialize is absent). `getRosters()` from a
Perspective button proves roster writes. The alarm status table component
shows active alarms without any pipeline at all.
