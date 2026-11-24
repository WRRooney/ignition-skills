# Pages, docks, and session props

## Pages and docks

```bash
ign page list --project Demo [--json]
ign page mount --project Demo --url /overview --view-path Pages/Overview --title Overview
ign page mount --project Demo --url /overview --view-path Pages/Overview --dock left:Navigation/Menu:260 --dock top:Navigation/Header:48
ign page mount --project Demo --url /overview --view-path Pages/Overview --no-docks
ign page shared-dock --project Demo --dock top:Navigation/Header:48 --remove left
ign page unmount --project Demo --url /overview
ign page delete --project Demo --confirm            # whole resource; child then inherits its parent's pages
```

`--dock` is `side:viewPath[:size]`, repeatable; omitting it keeps existing docks.
Only one dock per side is laid out; stacked chrome belongs in rows inside one
docked view. URL param rules (no catch-all, percent-encode nested paths as one
segment) and popup shapes are in `page-routing-and-docks.md`. Page-config and session-props inherit per RESOURCE: a child project
holding any of its own shadows the parent's entirely, and an empty directory
counts (`resource-scope-and-reload.md`).

## Session props

```bash
ign session-props declare --project Demo --file /tmp/props.json          # {"nav": {"selected": ""}} merged in
ign session-props declare --project Demo --prop-config /tmp/pc.json      # bindings / onChange on session props
ign session-props undeclare --project Demo --name nav                    # drops the prop AND its bindings
ign session-props delete --project Demo --confirm                        # whole resource
```

Read and write them in component scope as `self.session.custom.<path>`.
`system.perspective.getSessionProperty` / `setSessionProperty` do not exist.
A library function has no session; keep library functions pure and do session
I/O in the component script. Nested-click hand-offs, page-scoped messaging, and
which state belongs in the session are in `session-props-and-messaging.md`.
