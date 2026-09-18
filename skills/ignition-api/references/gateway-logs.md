# The gateway log is the first diagnostic

`ign logs` wraps `GET /data/api/v1/logs`, which returns gateway log entries
with level, logger, message, age, and, for errors, the Java or Jython stack.

```
ign logs --search <text> --min-level ERROR --limit 20 --stack
ign logs --logger plant.nav --since-min 15
```

Filter by logger name to isolate one script: a library module that calls
`system.util.getLogger("plant.nav")` is searchable by that name.

## Wrong

Guessing why a view is empty by re-scanning, restarting, or rewriting; or
reading an old error as a current one. Entries persist, so an initialization
error from hours ago may describe a bug already fixed. Compare the entry age
with the time of the last write (`--since-min`).

## Right

After any scan that touches a script, query the log. Messages to know:

| Message | Meaning |
|---|---|
| `Could not initialize project script module '<pkg.mod>'` plus a `PyException` | the module is structurally wrong or has a syntax error |
| `Error creating dataFile ... NoSuchFileException` | a `resource.json` lists a file that does not exist (typically `thumbnail.png`); persists until a restart even after the manifest is fixed |
| `AttributeError: 'module' object has no attribute ...` on `system.*` | an 8.1 or invented function; see the ignition-view skill's 8.3 correctness reference |
| `Tag already exists, and 'abort' collision policy has been specified` | a config scan re-submitted an existing type; harmless unless instances export as `Unknown` |
| `perspective.ClientSession :: WebSocket disconnected` | a headless session closed; not an error in your view |
| `IllegalArgumentException: Provider not found:` | a script resolved the default provider from an empty tag path |

Third-party module errors (an MQTT payload handler, for example) share the log;
filter by your logger or path.

## Verify a script ran

Put a `logger.info("buildNavTree: %d browsed, %d matched" % ...)` in any script
whose result you cannot observe headlessly. Its presence in the log after a
real session proves the code ran and shows the counts; its absence means the
trigger (an `onStartup`, a button) never fired.
