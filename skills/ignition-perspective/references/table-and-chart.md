# Table and chart gotchas

All three produce a wrong render with no console error, no crashed component, and
nothing in the gateway log. Budget debugging time accordingly.

## A dict cell reaches a column subview as a Python repr string

A dataset cell holding a dict arrives in the column's subview as
`u"{'ackTime': '', 'isAcked': False}"`, not as an object. `{view.params.value.isAcked}`
in an expression yields null, the cell renders the word "null" under a red quality
overlay, and `position.display` cannot hide it.

Fix: put a JSON string in the cell (`json.dumps` in the script that builds the
rows) and `json.loads` it in the subview through a script transform or an event
script, never an expression. A Java `Map` also reaches Jython with a one-argument
`get()`, so `.get(k, default)` raises; going through `json.loads` avoids that too.

## `ia.chart.*` colors must be literal hex

A canvas cannot resolve a CSS custom property. Hand a series, axis, or pie
`var(--info)` and the chart draws solid black. Keep every other color on theme
tokens; write out only the chart ones, sampled from the theme's `variables.css`
(`ign theme copy-base` makes the module's base themes readable).

## `ia.chart.xy` needs the whole series and axis tree

An XY axis needs `name` and `render`, and a series binds to an axis by that name
(`"yAxis": "value"`). Emitting only the fields that differ from the defaults also
renders an empty black chart; the charting library wants the full shape. Start from
a chart that already works (a Designer export), deep-copy it, and fill in data,
names, labels, render, and color. The x-axis `render` is `"date"` (with
`date.inputFormat` matching the string the rows carry) or `"category"`.

## `ia.display.tree` has no events

Its props reducer reads only `selection` (bidirectional array) and
`selectionData`, so it cannot host row menus, inline buttons, or drag. A tree that
needs any of those is hand-built from flex repeaters. Verify a component's event
surface before designing on it.

## Power Chart pens are historian references

A pen's `data.source` is
`histprov:<historian>:/drv:<gateway>:<provider>:/tag:<path>`, not a binding. It
resolves only if that historian provider exists and the tag is historized
(`historyEnabled: true` with that provider). A gateway with no history provider
(`historian-provider` resources empty) draws nothing; create one first. No REST
endpoint returns the `<gateway>` system-name segment; read it from the gateway
web UI or from an exported chart. An unresolved pen is an empty plot with no
console error, so historize a tag for a few minutes before judging a render.
