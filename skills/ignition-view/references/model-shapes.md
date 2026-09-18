# Model shapes the SDK enforces

Wire shapes Ignition 8.3 accepts; the Pydantic models reject the wrong form at
author time.

## Events live under a category layer

```json
"events": {"component": {"onActionPerformed": {"type": "script", "scope": "G", "config": {"script": "..."}}}}
```

`events -> category ("component" | "dom") -> eventName -> handler`. A view with
`{"events": {"onActionPerformed": ...}}` (no category) does not open.
`Component.add_event(category, name, handler)` builds the three layers; handlers
are `ScriptEventHandler`, `NavEventHandler`, or `PopupEventHandler` from
`ignition_gen_sdk.models.views.events`. A script handler body is checked against the
`system.*` catalog; unknown calls raise. Wire shapes: script
`{"type": "script", "scope": "G", "config": {"script": "<tab-indented body>"}}`,
navigation `{"type": "nav", "scope": "G", "config": {"url": "/pumps", "newTab": false}}`,
popup as in `page-routing-and-docks.md`. An unmodeled handler type rejects the
whole view on load.

## View params are bare scalars

Correct: `{"params": {"tagPath": "[default]Tanks/T01"}}`.
Wrong: `{"params": {"tagPath": {"value": "", "dataType": "String"}}}` (that is the
UDT parameter shape; the `View` model rejects it).

## Binding type literal

`"property"`, never `"prop"`. The expression binding discriminator is `"expr"`;
the expression transform is `"expression"`; the structure binding is `"expr-struct"`.
They are not interchangeable. The full discriminator table and the propConfig
wrapper rule are in `binding-discriminators.md`.

## No bindings for static values

A constant belongs in `props` as a plain value. `bind_expression()` raises
`StaticBindingError` on an expression with no `{` and no `(`. For a constant style
class pass it at construction, `vb.label(text="Flow", style={"classes": "eng-units"})`,
or use `component.set_prop("props.style.classes", "eng-units")`. A dynamic class
stays an expression binding.

## propConfig entry flags

`persistent: true` beside a binding and flag-only entries such as
`{"access": "PROTECTED", "persistent": true}` are first class:
`bind_property(..., persistent=True, access="PROTECTED")`, same kwargs on
`bind_tag` and `bind_expression`. A `--file` round trip preserves them.

## Map transform

```json
{"type": "map", "inputType": "scalar", "outputType": "scalar",
 "mappings": [{"input": true, "output": "ON"}, {"input": false, "output": "OFF"}],
 "fallback": "-"}
```

`outputType` is one of `scalar`, `expression`, `color`, `inline-style`,
`style-list`, `document`. Use `style-list` when the target is `props.style.classes`
and `color` when driving an SVG `fill.paint`. An older `{"inputs": [...]}` shape
does not run. `Component.map({...})` builds this; a `fallback` key in the dict
becomes the transform fallback.

## Format transform

```json
{"type": "format", "formatType": "numeric", "formatValue": "0.00"}
{"type": "format", "formatType": "datetime", "formatValue": {"date": "medium", "time": "short"}}
```

The key is `formatValue`, never `pattern`. `Component.format("0.00")` emits the
numeric form; build `FormatTransform(formatType="datetime", formatValue=FormatDatetimeConfig(...))`
for dates.

## Disable a binding in place

A binding that must not run but should survive keeps `"enabled": false` inside
the binding object, a sibling of `type` and `config`. Emit that instead of
deleting the binding when asked to turn it off. Same idea as `events.dom.onClick.enabled`.

## Drop targets

`props.dropConfig.udts[]` entries need `type` (UDT type id), `param` (the view
param that receives the path), and `action: "path"`. `vb.drop_udt("Pumps/Pump")`
emits one; a malformed entry is silently inert in the Designer, so the model
rejects it.

## Component-specific prop names

- `ia.display.markdown`: `props.source` is the content string; `props.markdown`
  is a render-options object (`escapeHtml`, `breaks`). Binding content to
  `props.markdown` renders nothing.
- `ia.display.view`: `props.path` and `props.params`. `viewParams` belongs only
  to page-config docks and popup event actions, which are different schemas.
