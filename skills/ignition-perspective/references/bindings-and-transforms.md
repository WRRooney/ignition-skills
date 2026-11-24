# Bindings and transforms

## Performance order

`property > expression > script transform > event script`, fastest to slowest.
Use the fastest tier that can express the value. Scripts only for genuine
cross-view navigation, multi-step writes, or discovery.

`runScript(...)` inside an expression is script tier, not expression tier: it runs
Jython on every evaluation. `bind_expression` emits a non-fatal
`BindingPerformanceWarning` when it sees one. Acceptable for load-time reads whose
inputs change rarely (a tooltip, a config lookup); wrong for anything that tracks
a process value.

## The view.custom data surface

Components never call `tag()` in an expression and never bind a tag directly when
the value is shared. Instead:

1. Declare `custom.<name>` at the view level.
2. Tag-bind it (`mode: "indirect"` when parameterized).
3. Property-bind component props to `{view.custom.<name>}`.

```python
vb.params(tagPath="")
vb.bind_custom_tag("level", "[default]{tagPath}/Level", mode="indirect")
value.bind_property("props.text", "view.custom.level")
```

Presentation (a class, a font size, a threshold) stays on the component: data to
custom, presentation to component. Swapping one card for another then costs
nothing; the new card binds to the same custom prop.

`vb.bind_custom_expression("isPending", 'indexOf({session.custom.q}, {view.params.tagPath}) >= 0')`
is the expression sibling and runs the same syntax guard. Do not hand-build a
`prop_config` dict for a binding the typed helpers already cover; the raw escape
hatch bypasses the guards.

## Indirect references

Two valid forms:

- Numbered: `tagPath: "{1}/Level"`, `references: {"1": "{view.params.tagPath}"}`.
  `bind_custom_tag` generates this when `references` is omitted, rewriting each
  bare `{param}` token to `{N}`.
- Named: `tagPath: "{tagPath}.meta_label"`, `references: {"tagPath": "{view.params.tagPath}"}`.
  Pass `references={...}` to use it verbatim.

A bare `{token}` is malformed only when no references entry resolves it; the
builder raises in that case. `references=` requires `mode="indirect"`.

Addressing inside a tag path: `/Member` is a member tag, `.prop` is a tag property,
so `{tagPath}/Level.engUnit` reads a member's property. Do not prepend a provider
to the template (`[default]{1}/Level`); put the qualified path in the param value.
Exact wire shapes for every binding and transform type: `binding-discriminators.md`.

## Bidirectional custom props are the write channel

For a one or two tag write, do not call `system.tag.writeBlocking` from an event
script. Bind `custom.<name>` with `bidirectional=True` and let the script assign
`self.view.custom.<name> = v`. For a multi-value command, model the payload as one
dict-shaped custom prop bound bidirectionally to a document tag plus a sibling
trigger bool. The same script then works for every instance because the bindings
are indirect through the view param.

Bidirectional bindings write back once on mount; in an anonymous session on a
write-protected provider that shows as a `Bad_ReadOnly` toast (environmental).

## Transform chaining

Transforms attach to the most recent `bind_*` call on that component:

```python
c.bind_tag("props.text", "[default]Tanks/T01/Level").format("0.0")
c.bind_property("props.style.classes", "view.custom.state").map({"running": "on", "stopped": "off", "fallback": ""})
c.bind_expression("props.text", "{view.custom.ts}").expression("dateFormat({value}, 'HH:mm')")
c.bind_property("custom.rows", "view.custom.raw").script("\tif value is None:\n\t\treturn []\n\treturn value")
```

Calling `bind_*` again starts a new chain. `.expression()` runs the expression
syntax guard; `.script()` takes verbatim Jython (tabs preserved).

## Other binding builders

`bind_expression_structure("props.arc", struct={...}, waitOnAll=True)`,
`bind_query(prop, queryPath, parameters=, polling_rate=, returnFormat=)`,
`bind_tag_history(...)`, `bind_http(...)`. Power Chart pens are historian
references, not bindings (`table-and-chart.md`).

## Fan-out

When one state drives several components, compute the class string once on a
view custom prop and property-bind every consumer to it: one expression, N
property reads, one edit site.
