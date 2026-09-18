# Resource scope, inheritance, and reload (view side)

Per-resource inheritance of `page-config` and `session-props`, the
empty-directory trap, and gateway-scope script reload are canonical in the
ignition-disk skill:
[`resource-inheritance-and-reload.md`](../../ignition-disk/references/resource-inheritance-and-reload.md)
and [`scan-endpoints.md`](../../ignition-disk/references/scan-endpoints.md).
What follows is the view-authoring consequence.

## What it means for `ign page` and `ign session-props`

- A child project holding ANY page-config or session-props of its own hides
  the parent's completely; a route or prop declared only on the parent is
  invisible in the child and every binding reading a parent-only session prop
  goes null. To share routes from an inheritable template, children hold no
  page-config: `ign page delete --project Child --confirm`.
- `ign session-props undeclare --project P --name X` removes the prop AND the
  propConfig entries under it. Dropping the prop alone leaves its binding
  declared and polling in every open session.
- Mount a validation probe in the project whose client will render it; a probe
  mounted in the parent returns "View Not Found" under a child that has its own
  page-config, and mounting into a child that has none recreates the resource
  with only the probe route.

## A scan reloads everything

`POST /data/api/v1/scan/projects` reloads views, pages, session props, and
project library `code.py` modules for Perspective scope. No reload gate, no
signature gate. When a view or script does not behave after a scan it is a
real initialization or runtime error, or empty data:

```bash
ign logs --search plant.nav --min-level ERROR --stack
ign logs --since-min 15 --min-level WARN
```

`Could not initialize project script module 'plant.nav'` with a traceback is
the usual shape. Gateway-scope callers (tag event scripts, timers) keep the
OLD module until a gateway restart, so verify edited library code from a
Perspective view, not a tag-to-tag probe.

## Loadable library module layout

```
ignition/script-python/plant/            package folder, NO resource.json
ignition/script-python/plant/nav/code.py
ignition/script-python/plant/nav/resource.json   scope "A", files ["code.py"], attributes.hintScope 2
```

- A `resource.json` inside the package folder makes the gateway treat the
  package as one empty script and hide every module beneath it; the Designer
  shows a single empty file named after the package.
- Without `hintScope` the module is silently skipped: no error, the module is
  undefined, every caller fails with an attribute error at runtime.
- Scope is `A` (all), unlike views (`G`). Do not emit
  `lastModificationSignature`; its absence does not stop the module loading.
- Space indentation becomes mixed indentation on the first in-Designer edit
  (the Designer inserts tabs) and an `IndentationError`.

`ign script write` emits this layout and rejects space-indented code.

## Moving resources moves their tests

Tests that load a live project script by path point at the old project after a
move and ERROR at setup, which reads as a green suite unless the error count is
checked. After any resource move, grep the test tree for the old project name
and expect zero errors, not just zero failures.
