---
name: ignition-scripts
description: Use when writing, editing, or deleting Ignition project library scripts (script-python, `ign script`) or gateway and session event scripts (startup, shutdown, timer, tag change, message handlers, `ign event`), or when checking any Jython code for API correctness (`ign builtins audit`, legacy functions that no longer exist). Triggers include "project script", "library script", "script-python", "code.py", "gateway event", "session event", "timer script", "tag change script", "message handler", "ign script", "ign event", "ign builtins", "system.* does not exist", "Jython". Do not use for script bodies inside a Perspective view's component events or transforms (author those with ignition-perspective, then audit here), named queries (use ignition-queries), or tag event scripts on a tag definition (use ignition-tag).
---

# Project and event scripts with `ign`

## Where they live

| Resource | Path | Verb |
|---|---|---|
| Library script | `projects/<name>/ignition/script-python/<path>/code.py` | `ign script` |
| Gateway event script | `projects/<name>/ignition/<event>/` | `ign event` |
| Session event script | `projects/<name>/com.inductiveautomation.perspective/<event>/` | `ign event` |

## Rules

1. Only `ign` writes these files; never hand-edit `code.py`, an event `.py`, or `resource.json`.
   If a needed shape is not expressible, stop and tell the user what is missing.
2. `--dry-run` first on every writing verb.
3. Writes scan projects automatically. Do not add a separate scan; `--no-scan` only when
   the gateway is unreachable.
4. Code is TAB-indented Jython 2.7; space-indented code is rejected. Unknown `system.*`
   calls are rejected at write time. Keep sources ASCII: a coding cookie is a
   `SyntaxError` in a project script.
5. After a write, check `ign logs --search <term> --min-level ERROR --stack --since-min 15`
   before theorizing (for example "Could not initialize project script module").

## Library scripts

```bash
ign script write --project Demo --script-path plant/nav --file /tmp/nav.py --dry-run
ign script replace-text --project Demo --script-path plant/nav --old "'Pumps'" --new "'Pump Stations'" --expect 1
ign script delete --project Demo --script-path plant/nav
```

The final path segment is the module directory holding `code.py` + `resource.json`;
package folders carry no `resource.json`. Scripts hot-reload for Perspective scope only;
gateway-scope callers (tag events, gateway events) keep the old module until restart.
A library function has no Perspective session: keep library functions pure and do
session I/O in the component script.

## Gateway and session event scripts

```bash
ign event kinds                                   # 18 kinds, function signature, settings
ign event list --project Demo
ign event write --project Demo --kind gateway.timer --name Poll --file /tmp/poll.py --attr delay=5000
ign event replace-text --project Demo --kind gateway.update --old readCache --new rebuildCache --expect 1
ign event delete --project Demo --kind gateway.timer --name Poll
```

Each event is a plain `<function>.py` + `resource.json`; the
file must define the Designer's exact function signature. Kinds, settings, singleton vs
named, and gotchas: `references/event-scripts.md`.

## API correctness

```bash
ign builtins audit --project Demo          # system.* calls and expression functions absent from the catalog; exit 1 if any
ign builtins audit --allow cirruslink      # accept a module-provided namespace
```

Run the audit after writing any script, including script bodies inside views.
Rename table and common traps: `references/api-correctness.md`.

## References

| File | Covers |
|---|---|
| `references/event-scripts.md` | Every gateway and session event kind: folder, function signature, resource.json settings, singleton vs named, which settings `ign event write` requires, update-script cache rebuild |
| `references/api-correctness.md` | `ign builtins audit`, legacy rename table, functions that do not exist, `system.tag.browse` vs `browseTags`, nested `typeId` filters, never swallow a browse |
| `references/jython-gateway-quirks.md` | Coding cookie `SyntaxError`, tab normalization, tag event script scope, `system.user` return values, `isAuthorized` tree semantics, provider-not-found |
