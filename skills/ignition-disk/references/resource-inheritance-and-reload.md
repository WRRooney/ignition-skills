# Per-resource inheritance and script reload scope

Two rules make a correct change look like it did nothing.

## page-config and session-props inherit per resource

A child project inherits its parent's `page-config` and `session-props`
only when it has none of its own. The moment the child holds its own copy
of either resource, the parent's is hidden completely; property-by-property
merging does not happen:

- a route added to the parent returns "View Not Found" in the child
- a session property declared only on the parent is invisible at runtime in
  the child, and every binding that reads it goes null

Fix by removing the child's copy (`ign session-props delete --project X
--confirm`, `ign page delete --project X --confirm`) or by declaring the same
routes and props in both.

- The Designer saves a page-config copy into whichever project is open, so
  working in the child in the Designer produces the shadow every time; check
  for an owned `page-config/` after any Designer session in a child.
- `ign page mount` into a child that has no page config recreates the resource
  with only the new route, so every inherited route vanishes. Mount routes and
  validation probes in the template, and validate them from the client of a
  project that inherits them.
- A template route may name a view that exists only in the child; it resolves
  at runtime in the child's scope.
- Alarm pipelines inherit like views; child shim pipelines set a base path and
  jump to a shared stage.

`ign session-props undeclare --project X --name Y` removes one property and
the `propConfig` entries under it. Removing only the property leaves its
binding declared and polling in every session.

## An empty directory is still a resource

Perspective treats the directory as the resource. A child holding an empty
`page-config/` shadows every parent route; no scan helps, and it looks
exactly like a stale cache that needs a restart. It is not. Delete the empty
directory and the routes resolve at once. Empty directories usually come
from a read command that created its target folder; the SDK's read paths
never do this now, but check for one before suspecting anything else when a
child route fails to resolve.

## Library scripts reload per scope

After `POST /scan/projects`:

| Caller scope | Sees the edited module |
|---|---|
| Perspective (bindings, component events, session scripts) | within seconds |
| Gateway (tag event scripts, timer scripts, alarm pipelines) | no; the old module keeps running until a gateway restart |

Consequences:

- A tag-to-tag probe (write a trigger tag, let a tag event script run, read a
  result tag) is trustworthy only for the first run after a restart.
- To verify edited library code, exercise it from a Perspective view.
- Gateway-scope scripts can only reach a project's library when that project
  is the gateway scripting project (Gateway settings).

## Everything else reloads on scan

Views, pages, session props, style classes, and Perspective-scope library
modules load on `/scan/projects` with no reload or signature gate. A resource
that is still invisible after a scan is malformed (a package folder with a
`resource.json`, a module without `hintScope`, a view nested inside a view's
directory) or has a runtime error in `ign logs`; do not wait for a reload and
do not restart.
