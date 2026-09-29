# Gateway and session event scripts

In 8.3 every project event script is a directory holding `<function>.py` and a
`resource.json` (`scope: "G"`, `files: ["<function>.py"]`). Settings live in
`resource.json` `attributes` next to `enabled`. 8.1 stored all gateway events in one
gzipped binary `ignition/event-scripts/data.bin`; that file does not exist in 8.3.

Gateway events live under `projects/<p>/ignition/`, session events under
`projects/<p>/com.inductiveautomation.perspective/`. Singleton kinds sit directly in
the folder; named kinds hold one subdirectory per event.

| Kind | Folder | Function | Settings (`attributes`) |
|------|--------|----------|-------------------------|
| `gateway.startup` | `startup/` | `onStartup()` | |
| `gateway.shutdown` | `shutdown/` | `onShutdown()` | |
| `gateway.update` | `update/` | `onUpdate(actor, resources)` | |
| `gateway.timer` | `timer/<name>/` | `handleTimerEvent()` | `delay` (ms), `fixedDelay`, `sharedThread` |
| `gateway.tag-change` | `tag-change/<name>/` | `onTagChange(initialChange, newValue, previousValue, event, executionCount)` | `paths` (list), `changeTypes` (`ValueChange`, `QualityChange`, `TimestampChange`) |
| `gateway.scheduled` | `scheduled/<name>/` | `handleScheduleEvent()` | `cronExpression` |
| `gateway.message` | `message/<name>/` | `handleMessage(payload)` | `threadType` (`Shared`) |
| `session.startup` | `startup/` | `onStartup(session)` | |
| `session.shutdown` | `shutdown/` | `onShutdown(session)` | |
| `session.page-startup` | `page-startup/` | `onPageStartup(page)` | |
| `session.accelerometer` | `accelerometer/` | `onAccelerometerDataReceived(session, data, context)` | |
| `session.auth-challenge` | `auth-challenge/` | `onAuthChallengeCompleted(session, payload, result)` | |
| `session.barcode` | `barcode/` | `onBarcodeDataReceived(session, data, context)` | |
| `session.bluetooth` | `bluetooth/` | `onBluetoothReceived(session, data)` | |
| `session.nfc-scan` | `nfc-scan/` | `onNdefDataReceived(session, data, context)` | |
| `session.form-submission` | `form-submission-handler/<name>/` | `handleSubmission(session, name, data, files, formContext, sessionContext, retry)` | |
| `session.key-event` | `key-event/<name>/` | `onKeyEvent(page, event)` | `eventBound` (`KEY`), `eventBoundKey`, `eventBoundCode`, `eventMode` (`KEYUP`), `regexPattern`, `regexWindow`, four `*EventModifier` flags, three `*EventOption` flags |
| `session.message` | `message/<name>/` | `handleMessage(session, payload)` | `threadType` (`Shared`) |

## Writing with `ign event`

- `--attr key=JSON` is repeatable; a bare word is a string, so
  `--attr cronExpression=0 2 * * *` works. `--attrs-file` takes a JSON object.
- The code must define the function with the exact parameter list above. The
  gateway calls it by position, so a renamed or reordered parameter is a silent bug.
- A rewrite keeps the event's existing settings and `enabled` unless overridden.
  Unknown or mistyped settings are refused.
- Settings with no safe default are required on create: tag-change `paths`,
  scheduled `cronExpression`, and every key-event setting (copy them from an
  existing key event with `ign event list --json`).
- The body runs the library-script gate: TAB indentation, syntax, known `system.*`.

## Behavior

- Gateway events run in gateway scope for every runnable project. An inheritable
  parent's events run in each child that does not override them, so a parent's
  update script can run once per child project on one save.
- The update script fires on every project save and every `POST /scan/projects`,
  including the scan each `ign` write triggers. It is the fallback hook for
  rebuilding caches built in gateway scope. Anything it writes to the data dir
  (a cache file, a memory tag's value in `tags.json`) changes on every scan.
