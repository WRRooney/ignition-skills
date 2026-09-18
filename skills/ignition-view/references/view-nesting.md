# Views cannot nest inside another view's directory

Never put a view at `A/B` when a view already exists at `A`. On disk that places
`views/A/B/view.json` inside `views/A/`, which is itself a resource directory
(`view.json` + `resource.json`), and Perspective will not load the inner one.

Symptom: the nested view renders as a dashed box with a warning triangle wherever
it is embedded (a table column subview, an `ia.display.view`, a page). No console
error, no `component_crashes`, no gateway log line; `ign view validate` reports a
clean render. Sibling views written in the same run load fine, which makes it look
like a problem with that one view's content.

Convention: a path segment that holds views is a plain folder. The page is a leaf
and its atoms live in sibling folders:

```
Pages/Alarm/Editor            view
Pages/Alarm/Row/Edit          view
Pages/Alarm/Popup/Editor      view
Pages/Alarm/Chip              view
```

not `Pages/Alarm` (view) with `Pages/Alarm/Row` under it.

## Audit

```bash
V=projects/Demo/com.inductiveautomation.perspective/views
for d in $(find "$V" -name view.json | sed "s|$V/||;s|/view.json||"); do
  [ -f "$V/$(dirname "$d")/view.json" ] && echo "NESTED: $d"
done
```

The expected count is zero.

## Same family: the resource directory is what Perspective resolves

An empty `page-config/` or `session-props/` directory in a child project is a
resource and shadows the parent's (see `resource-scope-and-reload.md`). In both
cases the directory layout, not the URL or the JSON, decides what loads.
