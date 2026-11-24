---
name: ignition-perspective
description: Use when authoring, editing, validating, or removing Ignition Perspective resources with the `ign` CLI and `ignition_gen_sdk` library. Covers views (flex/coord/split/tab/breakpoint/column roots, components, bindings, transforms, component events), page-config (mount pages, docks, shared docks), session props, style classes, the project stylesheet, themes, headless runtime validation, the `ia.*` component type inventory, and icon glyph names. Trigger phrases - "perspective view", "write view", "view.json", "faceplate", "embedded view", "flex repeater", "mount page", "dock", "session prop", "style class", "stylesheet", "theme", "validate view", "ign view", "ign page", "list components", "ia.* types", "palette", "icon names", "ign icons".
---

# Perspective resources with `ign`

Covers `projects/<name>/com.inductiveautomation.perspective/**` and themes under
`config/resources/core/com.inductiveautomation.perspective/themes/`. Library and event
scripts: `ignition-scripts`. Named queries: `ignition-queries`. Script bodies inside a view
follow the Jython and API-correctness rules in `ignition-scripts`.

## Rules

1. Only `ign` verbs (or a committed generator using the SDK models) write Perspective files.
   Never hand-edit `view.json`, `resource.json`, `page-config`, or `style.json`. If a shape
   is not expressible, stop and tell the user what is missing.
2. `--dry-run` first on every writing verb.
3. Writes scan automatically; do not add a scan. `--no-scan` only when the gateway is
   unreachable. A scan reloads everything, so misbehavior after a scan is a real runtime
   error or empty data.
4. Check `ign logs --search <term> --min-level ERROR --stack --since-min 15` before theorizing.
5. Generators are seeds: never re-run one over a view edited in the Designer.
6. Model-valid is not rendered: finish with `ign view validate`.

## Tasks

Read the reference for the task; it holds the commands and examples.

| Task | Reference |
|---|---|
| Build, write, edit, or delete a view; naming and prop scopes | `references/view-authoring.md` |
| Mount pages, docks, session props | `references/pages-and-session-props.md` |
| Style classes, project stylesheet, themes | `references/styles-and-themes.md` |
| Validate a rendered view headlessly | `references/runtime-validation.md` |
| Find an `ia.*` type, its model, or icon names | `references/component-inventory.md`, `references/palette-model-map.md`, `references/icons.md` |

## Gotchas

Load only the file that matches the problem.

| Problem area | Reference |
|---|---|
| Wire shapes the models enforce (events, handlers, params, propConfig) | `references/model-shapes.md` |
| Exact binding JSON per type, transform shapes | `references/binding-discriminators.md` |
| Binding performance, `view.custom` data surface, indirect refs, bidirectional writes | `references/bindings-and-transforms.md` |
| Expression syntax and which expression functions exist | `references/expression-idioms.md` |
| Script transform fires with null on first mount | `references/discovery-transform-null-guard.md` |
| `onChange` vs message handlers | `references/onchange-vs-messages.md` |
| Child `position` keys per container, breakpoint containers | `references/container-positions.md` |
| Flex grow/shrink, repeater basis | `references/flex-sizing.md` |
| Flex repeater sizing and output params | `references/flex-repeater.md` |
| View at `A/B` under a view at `A` | `references/view-nesting.md` |
| Unknown props, exact prop names, label quirks | `references/component-prop-quirks.md` |
| Params and config data (keys, enums, input/output slots) | `references/params-and-config.md` |
| Persistent props and seeds | `references/persistent-props.md` |
| Session props, nested-click hand-off, page messaging | `references/session-props-and-messaging.md` |
| URL params, docks, popups | `references/page-routing-and-docks.md` |
| Per-resource inheritance, reload, library module layout | `references/resource-scope-and-reload.md` |
| Overlays, `pointerEvents`, popup openers, touch targets | `references/click-layering.md` |
| State styling with classes, SVG colors | `references/style-class-state-binding.md` |
| SVG pipes, mirroring, animation | `references/svg-graphics.md` |
| `ia.symbol.*` orientation and blank valves | `references/symbols.md` |
| Table cells, `ia.chart.*`, Power Chart pens | `references/table-and-chart.md` |
| ApexCharts module | `references/apexcharts-module.md` |
| Drag and drop | `references/drag-and-drop.md` |
