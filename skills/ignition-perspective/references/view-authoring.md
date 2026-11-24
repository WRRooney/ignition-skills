# Authoring a view

Build the view with `ViewBuilder`, write it with `ign view write`, then validate
(`runtime-validation.md`). Wire shapes: `model-shapes.md`, `binding-discriminators.md`.

## 1. Build the view with the library

```python
from ignition_gen_sdk.builders.view import ViewBuilder
from ignition_gen_sdk.models.views import FlexChildPosition
from ignition_gen_sdk.serializers.view_disk import view_to_disk
import json

vb = ViewBuilder()
vb.flex_root(direction="column", style={"gap": "8px"})
vb.params(tagPath="")                                   # bare scalar params only
vb.bind_custom_tag("level", "[default]{tagPath}/Level", mode="indirect")
vb.bind_custom_tag("running", "[default]{tagPath}/Running", mode="indirect")

title = vb.label(text="Pump", name="Title", style={"classes": "h2"})   # constant class: plain prop
value = vb.label(text="", name="Level")
value.bind_property("props.text", "view.custom.level").format("0.0")   # transforms chain off the last binding
state = vb.label(text="", name="State")
state.bind_expression("props.style.classes",
    'if({view.custom.running}, "state-running", "state-stopped")')     # single = for equality

json.dump(view_to_disk(vb.build()), open("/tmp/pump.json", "w"), indent=2)
```

Key facts about the builder API:

- Factory helpers (`label`, `button`, `image`, `icon`, `embedded_view`,
  `flex_repeater`, `power_chart`, `alarm_status_table`, `alarm_journal_table`)
  create a typed component, auto-attach it to the root, and **return the
  component**. `bind_*`, `set_prop`, and `add_event` are `Component` methods, so
  call them on that returned object, not on the builder.
- `flex_container(name=, direction=)` returns a standalone container that is NOT
  attached; append children to `.children` and pass it to `add_to_flex`.
- Props go by their camelCase wire name (`useDefaultViewHeight`, `readOnly`). A
  snake_case key whose camelCase form is a real prop raises at author time.
- `embedded_view(view_path=..., params={...})` emits `ia.display.view` with
  `props.path` and `props.params`.
- Six roots, each with a matching add helper:

| Root | Add helper | Position |
|------|-----------|----------|
| `flex_root(direction=)` | `add_to_flex(c, position=FlexChildPosition(...))` | basis/grow/shrink |
| `coord_root()` | `add_to_coord(c, position=CoordinatePosition(...))` | x/y/width/height |
| `split_root(orientation=)` | `add_to_split(c, side=)` | left/right/top/bottom |
| `tab_root(tabs=[...])` | `add_to_tab(c, tab_index=)` | tab index |
| `breakpoint_root(breakpoint=)` | `add_to_breakpoint(c, size=)` | large/small |
| `column_root()` | `add_to_column(c, basis=, grow=, height=, breakpoints=[ColumnBreakpoint(...)])` | column layout |

  `add_to_*` is idempotent by identity, so `vb.add_to_split(vb.label(text="L"), side="left")`
  attaches once and sets the position. Split, tab, breakpoint, and column children
  need a position; flex children do not.
- `tab_root(tabs=["Run", "Config"])` or `tabs=[TabSpec(text="Run"), TabSpec(text="Config", disabled=True)]`.
- Any `ia.*` type without a factory: construct `Component(type="ia.display.markdown", meta=Meta(name=...), props={...})`
  and add it with the matching `add_to_*`. `ign component list --flat` prints every known type
  (see Component inventory below).
- View-level data surface: `vb.custom(name, value)`, `vb.bind_custom_tag(...)`,
  `vb.bind_custom_expression(name, expr)`. Components then `bind_property("props.x", "view.custom.name")`.
- Events: `btn.add_event("component", "onActionPerformed", ScriptEventHandler(type="script", scope="G", config=ScriptEventConfig(script="...")))`.
  `NavEventHandler` and `PopupEventHandler` exist for `nav` and `popup` actions.

Full binding, transform, and model-shape rules: `bindings-and-transforms.md`,
`model-shapes.md`.

## 2. Write it with the CLI

```bash
ign view build --file /tmp/pump.json                                   # validate + print, no I/O
ign view write --project Demo --view-path Components/PumpFaceplate --file /tmp/pump.json --dry-run
ign view write --project Demo --view-path Components/PumpFaceplate --file /tmp/pump.json
```

`--file` runs the JSON through the `View` model, so a malformed view fails locally.
Without `--file`, `build` and `write` emit a fixed built-in demo view. `--doc-file`
sets the Designer documentation on `resource.json`; omitted, an existing view's
documentation is kept.

## 3. Small edits without a full rewrite

```bash
# one prop: seed value, persistent flag, or binding
ign view set-prop --project Demo --view-path Components/PumpFaceplate --prop custom.selected --no-persistent
ign view set-prop --project Demo --view-path Components/PumpFaceplate --component root/Level --prop props.text --value '""'
ign view set-prop --project Demo --view-path Components/PumpFaceplate --prop custom.level --binding-file /tmp/binding.json
ign view set-prop --project Demo --view-path Components/PumpFaceplate --prop custom.old --unset-binding

# exact literal text (a messageType, a style class, a token in a script body)
ign view replace-text --project Demo --view-path Components/PumpFaceplate --old state-stopped --new state-idle --expect 2 --dry-run

# remove
ign view delete --project Demo --view-path Components/PumpFaceplate --dry-run
```

`replace-text` matches the raw file, so quotes inside strings are escaped and `=`
is stored as `\u003d`. Prefer a token with neither and let `--expect` catch a miss.
Both verbs re-validate through the `View` model before writing.

## View naming and prop scopes

- View names: Title Case or PascalCase (`Pages/Overview`, `Components/PumpFaceplate`).
  Component names PascalCase, props camelCase, page URLs and style classes lowercase-dash.
- `params.*` are embed-time inputs; `custom.*` is internal state. Do not cross them.
- Data flows through `view.custom.*`: bind tags at the view level once, then
  property-bind components to `{view.custom.x}`. Presentation (a class, a font size)
  stays on the component.
- Writes go through a bidirectional `view.custom.*` tag binding, not
  `system.tag.writeBlocking` in an event script, when the write is one or two tags.
- Never put a view at `A/B` when a view exists at `A` (`view-nesting.md`).
