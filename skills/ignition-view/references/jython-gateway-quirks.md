# Jython and gateway scripting quirks (8.3)

## Project scripts

- Project scripts compile from a unicode string. A `# -*- coding: utf-8 -*-`
  cookie raises `SyntaxError: encoding declaration in Unicode string`, after
  which every entry point fails inside its binding transform with nothing
  reaching the module's logger; pages just render their empty state. Keep
  sources ASCII with `\uXXXX` escapes; `from __future__ import unicode_literals`
  is fine.
- Jython 2.7: no f-strings, no type hints. It accepts mixed tabs and spaces,
  but Python 3 test harnesses and `ign script write` refuse the file, and the
  Designer inserts tabs on edit. Normalize to whole tabs.
- Diagnose a silently failing module with a probe view whose transform calls
  the function inside `try/except` and logs `traceback.format_exc()`; remove
  the probe afterwards.
- Never `except Exception: return []` around a `system.*` call in a library
  function. Every empty-result mystery traced back to a swallowed exception.
  Log with a named logger (`system.util.getLogger("plant.nav")`) and return
  with the error visible; the logger name is then searchable with `ign logs`.
- Library scripts hot-reload for Perspective scope but not for gateway or
  tag-event scope (`resource-scope-and-reload.md`).

## Tag event scripts

Stored on the tag as `"eventScripts": [{"eventid": "valueChanged",
"script": "\t..."}]`, tab-indented. Scope: `tag`, `tagPath`, `previousValue`,
`currentValue`, `initialChange`, `missedEvents`, `event`. Self-resetting
trigger idiom:

```python
if currentValue.value:
	...
	system.tag.writeBlocking([event.tagPath], [False])
```

## System functions

- `system.tag.getConfiguration('' ...)` and any helper that resolves the
  default provider from an empty path throw
  `IllegalArgumentException: Provider not found:` in gateway and Perspective
  scope. Hard-code or configure the default provider name.
- `system.perspective.getProjectInfo()` returns `{description, lastModified,
  lastModifiedBy, name, pageConfigs, title, views}`; `name` is the session
  project and `views` includes views inherited from the parent.
- 8.3's gateway-api `ProjectManager` has no resource read; read resource bytes
  from `<dataDir>/projects/<name>/...` walking the `project.json` parent chain.
  `system.project.requestScan()` remounts every open view.
- `system.user.getUserSources()` returns user-source meta objects, not names;
  `str()` yields a Java identity string.
- `system.user.addUser`, `editUser`, `removeUser` return a `UIResponse`
  instead of raising. Read its errors; a rejected save otherwise looks like
  success. `removeRole` reports success for a role that never existed, and
  deleting a held role strips it from every member silently.
- The gateway's `allowUserAdmin: false` setting governs only the web UI user
  admin section; it does not block `system.user.*` writes.
- `system.perspective.isAuthorized` accepts a security-level tree: a
  descendant of a required level satisfies it, an ancestor does not; `AnyOf`
  needs one, `AllOf` needs all.
- Page-scoped `system.perspective.sendMessage` does not queue for views not
  yet mounted; use request/reply from the consumer's `onStartup`
  (`session-props-and-messaging.md`).
- A Java `Map` reaches Jython with a one-argument `get()`; go through
  `json.loads` or `dict(m)` first (`api-8-3-correctness.md`).
