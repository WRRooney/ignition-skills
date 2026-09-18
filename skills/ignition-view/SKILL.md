---
name: ignition-view
description: Use when authoring, editing, validating, or removing Ignition 8.3 Perspective project resources with the `ign` CLI and `ignition_gen_sdk` library. Covers Perspective views (flex/coord/split/tab/breakpoint/column roots, components, bindings, transforms, events), page-config (mount pages, docks, shared docks), session props, project library scripts, style classes, the project stylesheet, themes, named queries, and headless runtime validation. Trigger phrases - "perspective view", "write view", "view.json", "faceplate", "embedded view", "flex repeater", "mount page", "dock", "session prop", "project script", "style class", "stylesheet", "theme", "named query", "validate view", "ign view", "ign page". Do not use for database views, Vision windows, or tags (see ignition-tag).
---

# Perspective views and project resources with `ign`

## When to use

Any change under `projects/<name>/com.inductiveautomation.perspective/**` or
`projects/<name>/ignition/{script-python,named-query}/**`, plus Perspective themes
under `config/resources/core/com.inductiveautomation.perspective/themes/`.
The `ign` CLI (package `ignition_gen_sdk`) wraps every one of these with Pydantic
validation, a `--dry-run`, and an automatic gateway scan.

Environment: `ign` reads `IGNITION_URL`, `IGNITION_API_TOKEN`, and `IGNITION_DATA_DIR`
from the process environment or a `.env` in the working directory. Never echo the
token or pass it on a command line.

## Rules

1. **The SDK is the sole writer.** Every file under `projects/**` and
   `config/resources/**` is produced by an `ign` verb or by a committed generator
   that uses the same models. Never hand-write or hand-patch `view.json`,
   `resource.json`, `code.py`, `page-config`, or `style.json`. If a needed shape is
   not expressible, extend the Pydantic model or the CLI, then run the CLI.
2. **`--dry-run` first.** Every writing verb has one. Read the printed payload and
   target path before the real run.
3. **Disk writes scan automatically.** Project verbs `POST /data/api/v1/scan/projects`
   after a successful write; `theme` verbs scan config. Do not add a separate scan
   call. Pass `--no-scan` only when the gateway is unreachable.
4. **A scan reloads everything.** Views, pages, session props, and library scripts
   in Perspective scope all reload on scan. There is no reload gate. If something
   does not behave after a scan, it is a real runtime error or empty data.
5. **Check `ign logs` before theorizing.**
   `ign logs --search <term> --min-level ERROR --stack --since-min 15` returns the
   Jython traceback (for example "Could not initialize project script module").
6. **Generators are seeds.** A `build_*.py` generator writes a view family once.
   Never re-run one over a view that has since been edited in the Designer.
7. **Model-valid is not rendered.** Finish with `ign view validate` (see below).

## Authoring workflow

### 1. Build the view with the library

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
  and add it with the matching `add_to_*`. `ign component list --flat` prints every known type.
- View-level data surface: `vb.custom(name, value)`, `vb.bind_custom_tag(...)`,
  `vb.bind_custom_expression(name, expr)`. Components then `bind_property("props.x", "view.custom.name")`.
- Events: `btn.add_event("component", "onActionPerformed", ScriptEventHandler(type="script", scope="G", config=ScriptEventConfig(script="...")))`.
  `NavEventHandler` and `PopupEventHandler` exist for `nav` and `popup` actions.

Full binding, transform, and model-shape rules: `references/bindings-and-transforms.md`,
`references/model-shapes.md`.

### 2. Write it with the CLI

```bash
ign view build --file /tmp/pump.json                                   # validate + print, no I/O
ign view write --project Demo --view-path Components/PumpFaceplate --file /tmp/pump.json --dry-run
ign view write --project Demo --view-path Components/PumpFaceplate --file /tmp/pump.json
```

`--file` runs the JSON through the `View` model, so a malformed view fails locally.
Without `--file`, `build` and `write` emit a fixed built-in demo view. `--doc-file`
sets the Designer documentation on `resource.json`; omitted, an existing view's
documentation is kept.

### 3. Small edits without a full rewrite

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
is stored as `=`. Prefer a token with neither and let `--expect` catch a miss.
Both verbs re-validate through the `View` model before writing.

### View naming and prop scopes

- View names: Title Case or PascalCase (`Pages/Overview`, `Components/PumpFaceplate`).
  Component names PascalCase, props camelCase, page URLs and style classes lowercase-dash.
- `params.*` are embed-time inputs; `custom.*` is internal state. Do not cross them.
- Data flows through `view.custom.*`: bind tags at the view level once, then
  property-bind components to `{view.custom.x}`. Presentation (a class, a font size)
  stays on the component.
- Writes go through a bidirectional `view.custom.*` tag binding, not
  `system.tag.writeBlocking` in an event script, when the write is one or two tags.
- Never put a view at `A/B` when a view exists at `A` (`references/view-nesting.md`).

## Project resources

### Pages and docks

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
segment) and popup shapes are in `references/page-routing-and-docks.md`. Page-config and session-props inherit per RESOURCE: a child project
holding any of its own shadows the parent's entirely, and an empty directory
counts (`references/resource-scope-and-reload.md`).

### Session props

```bash
ign session-props declare --project Demo --file /tmp/props.json          # {"nav": {"selected": ""}} merged in
ign session-props declare --project Demo --prop-config /tmp/pc.json      # bindings / onChange on session props
ign session-props undeclare --project Demo --name nav                    # drops the prop AND its bindings
ign session-props delete --project Demo --confirm                        # whole resource
```

Read and write them in component scope as `self.session.custom.<path>`.
`system.perspective.getSessionProperty` / `setSessionProperty` do not exist in 8.3.
A library function has no session; keep library functions pure and do session
I/O in the component script. Nested-click hand-offs, page-scoped messaging, and
which state belongs in the session are in `references/session-props-and-messaging.md`.

### Project library scripts

```bash
ign script write --project Demo --script-path plant/nav --file /tmp/nav.py --dry-run
ign script replace-text --project Demo --script-path plant/nav --old "'Pumps'" --new "'Pump Stations'" --expect 1
ign script delete --project Demo --script-path plant/nav
```

Code must be TAB-indented Jython 2.7; space-indented code is rejected. Unknown
`system.*` calls are rejected at write time. Keep sources ASCII (a coding cookie
is a `SyntaxError` in a project script; `references/jython-gateway-quirks.md`). The final path segment is the module
directory holding `code.py` + `resource.json`; package folders carry no
`resource.json`. Scripts hot-reload for Perspective scope only; gateway-scope
callers (tag events) keep the old module until restart.

### Style classes, stylesheet, themes

```bash
ign style-class list --project Demo
ign style-class write --project Demo --name state-running --file /tmp/running.json   # {"base": {"style": {...}}, "variants": [...]}
ign style-class write --project Demo --file /tmp/family.json                           # {"name": payload, ...} bulk
ign style-class delete --project Demo --name state-running

ign stylesheet show --project Demo
ign stylesheet upsert --project Demo --marker pump-flash --file /tmp/flash.css          # replaces only that block
ign stylesheet remove --project Demo --marker pump-flash

ign theme list
ign theme copy-base                                                  # read-only copies of light/dark to learn token names
ign theme write --name plant-dark --dir /tmp/plant-dark --entrypoint index.css --description "..."
ign theme delete --name plant-dark
```

`style.json` carries only `base` and `variants`; any other key fails loud.
`variants[].pseudo` accepts CSS pseudo-classes only (`hover`, `disabled`, ...), so
data-driven state is one class per state plus a `style.classes` binding
(`references/style-class-state-binding.md`). Stylesheet selectors use the
`.psc-<class>` prefix; view JSON references the class unprefixed. The stylesheet is
the only channel for `@keyframes` because `ia.display.markdown` strips `<style>`.
Copies made by `theme copy-base` are ignored by the gateway; put overrides in a
theme of your own that `@import`s them.

### Named queries

```bash
ign named-query list --project Demo
ign named-query write --project Demo --query-path Reports/PumpRuntime --file /tmp/runtime.sql \
    --database PlantDB --param start:DateTime --param end:DateTime --type Query --cache-seconds 0
ign named-query delete --project Demo --query-path Reports/PumpRuntime
```

Every `:name` in the SQL must be declared with `--param` and vice versa. Ignition
scans SQL comments for parameters too, so keep `:word` tokens out of them.

## Runtime validation

```bash
ign page mount --project Demo --url /probe --view-path Components/PumpFaceplate
ign view validate --project Demo --page probe          # screenshot lands at .ign/validate.png
ign page unmount --project Demo --url /probe
```

`validate` drives headless Chrome against `/data/perspective/client/<project>/<page>`
(read-only, no token). `--base` defaults to `IGNITION_URL`; `--out` defaults to
`.ign/validate.png`. Exit 1 on `component_crashes` (React error boundaries, a
real bug) or a "View Not Found" placeholder; exit 0 with warnings on
`quality_error_overlays` (bad tag quality), console errors, and `symbol_svg_empty`.
Read the screenshot. A `page list` URL maps to `--page` by dropping the slash; the
root page is `--project` with no `--page`. Requires the `runtime` extra
(`uv tool install 'ignition-gen-sdk[runtime]'`) and `playwright install chrome`
(exit 2 otherwise).

Blind spots: view `onStartup` never completes headlessly, the session is anonymous
(tag writes fail with `Bad_ReadOnly`, `system.tag.getConfiguration` returns nothing on
a provider that requires authentication), nested views and dangling `{view.custom.x}`
references pass clean. Details: `references/runtime-validation.md`.

Scratch probe views and mounts are removed once the check is done
(`ign view delete` + `ign page unmount`).

## Gotchas index

Load only the file that matches the problem.

| Reference | Covers |
|-----------|--------|
| `references/model-shapes.md` | Wire shapes the models enforce: events under `events.component`, handler shapes, scalar params, `"property"` not `"prop"`, no static bindings, propConfig flags, map/format transform schemas, `enabled: false`, dropConfig |
| `references/binding-discriminators.md` | Exact JSON per binding type (`tag`, `property`, `expr`, `expr-struct`, `query`, `tag-history`, `http`), propConfig wrapper, transform shapes, reference addressing, `onChange` script shape |
| `references/bindings-and-transforms.md` | Performance order, view.custom data surface, indirect references (numbered and named), transform chaining, bidirectional writes, `runScript` cost |
| `references/container-positions.md` | Per-container child `position` keys, tab forms, `ia.container.breakpt` rules (two children, non-matching branch unmounted), embed `useDefaultView*` hygiene |
| `references/flex-repeater.md` | Repeater sizing, the ignored root position, output params write back only into seeded keys, instances from a keyed dict |
| `references/component-prop-quirks.md` | Unknown props kept and ignored, exact type strings and prop names, label ellipsis and color, text-field events, portal-rendered chrome |
| `references/session-props-and-messaging.md` | Declared session props, nested-click hand-off via session prop, view state across scans, page-scoped request/reply, docked relay |
| `references/page-routing-and-docks.md` | URL param splitting and encoding, params reach only the primary view, no `page.custom`, dynamic tab title, one dock per side, popup shapes |
| `references/click-layering.md` | Overlay z-order and `pointerEvents`, popup opener idiom with a stable ID, shared ad hoc trend, touch targets |
| `references/svg-graphics.md` | Stretchable pipe runs, two-SVG orientation with CSS mirror, SMIL and keyframe animation, symbol sizing in cards |
| `references/jython-gateway-quirks.md` | Coding cookie `SyntaxError`, tab normalization, tag event script scope, `system.user` return values, `isAuthorized` tree semantics, provider-not-found |
| `references/apexcharts-module.md` | Third-party ApexCharts component: formatter syntax, per-series array counts, static series skeleton, boolean state trend |
| `references/expression-idioms.md` | Single `=` equality, case-insensitive functions, 8.3 replacements for `length`/`contains`/`substringAfterLast`, bad-quality guards, preferred idioms, `expr-struct` nulls, relative tag paths |
| `references/api-8-3-correctness.md` | `ign builtins audit`, 8.1 to 8.3 rename table, functions that do not exist in 8.3, `system.tag.browse` vs `browseTags`, nested `typeId` filters, never swallow a browse |
| `references/persistent-props.md` | Unbound persistent props are live seeds, bound snapshots are noise, gate props keep their undecided sentinel, null seed ban, `currentBreakpoint`, dangling refs |
| `references/discovery-transform-null-guard.md` | Script transforms fire with null on first mount; empty path means provider root; guard before any browse/query |
| `references/params-and-config.md` | Object keys never start with a digit, `idx<n>_<name>` sortable keys, config and copy in Designer-editable data not code, enum params via `lower()` + map, input/output param slots, `value` cell param |
| `references/flex-sizing.md` | grow/shrink rules, repeater `basis: auto`, `defaultSize`, `position.display` vs `style.display`, do not emit defaults, repeater layout as one object param |
| `references/style-class-state-binding.md` | One class per state, fan-out through a custom prop, style classes painting SVG, built-in symbol CSS variables, stylesheet path |
| `references/symbols.md` | `ia.symbol.valve` orients via `props.valve`; valve blank on a cold session is a client race, not a view bug |
| `references/table-and-chart.md` | Dict cells arrive as a Python repr string, `ia.chart.*` cannot read CSS variables, XY charts need the full series/axis tree, Power Chart pen source strings |
| `references/view-nesting.md` | A view inside another view's directory renders a dashed placeholder with no error; audit script |
| `references/resource-scope-and-reload.md` | View-side consequences of per-resource inheritance (canonical text in ignition-disk), scan reloads everything, loadable library module layout, moving tests |
| `references/runtime-validation.md` | What `ign view validate` reports, URL mapping, health sweeps, blind spots |
| `references/icons.md` | Where 8.3 icon sprites live, `ign icons list`, invalid icon path crashes the component, empty embed path logs the same error |
| `references/drag-and-drop.md` | Native drag events never fire; simulate with mouse events; `ia.display.tree` has no events |
| `references/onchange-vs-messages.md` | A property `onChange` clears state before a message handler reads it; never watch transient interaction props |
