---
name: ignition-component
description: Use when the agent needs the inventory of Ignition 8.3 Perspective component type strings (ia.display.*, ia.input.*, ia.navigation.*, ia.symbol.*, ia.chart.*), wants to filter them by palette, needs to know which Pydantic model in the SDK backs a given ia.* type, or needs valid icon glyph names (material/ignition sprite sets) for an Icon component. Triggers include "list components", "component types", "ia.* types", "palette", "which chart types", "discriminator", "is there a model for", "icon names", "ign icons". Do not use for React, Vue, or any UI component outside Ignition Perspective, and not for authoring a view (use the view skill).
---

# Perspective component inventory

`ign component list` prints every `ia.*` type string the SDK's typed
component union knows. It reads the bundled inventory and never calls the
gateway, so it works offline and needs no token.

## Command surface

```
ign component list [--flat] [--json] [--palette NAME] [--no-color]
```

| Option | Output |
|---|---|
| (none) | Grouped by palette with `# palette` headers |
| `--flat` | One type per line, no headers (grep-friendly) |
| `--json` | `{"palette": ["ia....", ...]}` |
| `--palette NAME` | Only that palette; unknown names print an error listing the valid ones |
| `--no-color` | Plain headers (`NO_COLOR` env works too) |

Flags combine: `ign component list --palette input --flat`.

## Palettes

The palette is the middle segment of the type string, so there are exactly
five: `chart`, `display`, `input`, `navigation`, `symbol` (61 types total).

| Palette | Count | Examples |
|---|---|---|
| `chart` | 7 | `ia.chart.timeseries`, `ia.chart.xy`, `ia.chart.powerchart`, `ia.chart.gauge`, `ia.chart.simple-gauge`, `ia.chart.pie`, `ia.chart.chartrangeselector` |
| `display` | 29 | `ia.display.label`, `ia.display.icon`, `ia.display.table`, `ia.display.markdown`, `ia.display.view`, `ia.display.flex-repeater`, `ia.display.alarmstatustable` |
| `input` | 17 | `ia.input.button`, `ia.input.text-field`, `ia.input.dropdown`, `ia.input.toggle-switch`, `ia.input.numeric-entry-field`, `ia.input.date-time-picker` |
| `navigation` | 3 | `ia.navigation.link`, `ia.navigation.menutree`, `ia.navigation.horizontalmenu` |
| `symbol` | 5 | `ia.symbol.motor`, `ia.symbol.pump`, `ia.symbol.sensor`, `ia.symbol.valve`, `ia.symbol.vessel` |

Embedding components (Embedded View, Flex Repeater, View Canvas, Accordion,
Carousel) carry `ia.display.*` type strings, so they list under `display`;
there is no `embedding` palette on the command line even though the models
live in their own file. The symbol prefix is singular (`ia.symbol.`).

## How types map to models

Each type string is a `Literal` on exactly one Pydantic class under
`ignition_gen_sdk/models/views/components/`. The package's `ComponentUnion` is a
callable-discriminated union: it reads `type` from incoming JSON, routes to the
matching class, and falls back to `GenericComponent` (extra fields allowed, no
`Literal` on `type`) for any unknown or future `ia.*` string. `ign component
list` derives its inventory from the same union entries, so the CLI output and
the model set cannot drift.

| File | Palette | Classes |
|---|---|---|
| `display.py` | display | `Label`, `Icon`, `Image`, `Markdown`, `Progress`, `Table`, `Tree`, `TagBrowseTree`, `AlarmJournalTable`, `AlarmStatusTable`, `Barcode`, `Audio`, `VideoPlayer`, `PdfViewer`, `Map`, `Iframe`, `Sparkline`, `LinearScale`, `LedDisplay`, `MovingAnalogIndicator`, `CylindricalTank`, `Thermometer`, `Dashboard`, `EquipmentSchedule` |
| `embedding.py` | display | `EmbeddedView` (`ia.display.view`), `FlexRepeater`, `ViewCanvas`, `Accordion`, `Carousel` |
| `input.py` | input | `Button`, `Checkbox`, `Dropdown`, `Slider`, `TextField`, `TextArea`, `NumericEntryField`, `DateTimeInput`, `DateTimePicker`, `RadioGroup`, `ToggleSwitch`, `MultiStateButton`, `OneShotButton`, `PasswordField`, `FileUpload`, `SignaturePad`, `BarcodeScannerInput` |
| `navigation.py` | navigation | `Link`, `MenuTree`, `HorizontalMenu` |
| `symbols.py` | symbol | `Motor`, `Pump`, `Sensor`, `Valve`, `Vessel` |
| `chart.py` | chart | `Pie`, `TimeSeries`, `XY`, `PowerChart`, `Gauge`, `SimpleGauge`, `ChartRangeSelector` |
| `_generic.py` | any | `GenericComponent` fallback |
| `pipe.py` | none | `Pipe`, `PipeOrigin`: a pipe network entity inside a container's props, not a component |

Every typed class pairs with a `<Name>Props` model holding the component's
`props`. The full type-to-class table is in
`references/palette-model-map.md`.

Embedded View params are `props.params`, not `props.viewParams`; the latter
is ignored by the runtime and renders every param as null.

## Icon glyph names: `ign icons list`

Perspective 8.3 keeps its icon sprites inside the Perspective module jar, not
on disk. `ign icons list` extracts them and prints valid glyph names for an
Icon component's `props.path` (`material/home`, `ignition/...`).

```
ign icons list (--modl PATH | --container NAME) [--set material|ignition|symbol_...|all] [--json]
```

| Option | Meaning |
|---|---|
| `--modl PATH` | Path to `Perspective-module.modl` on the local filesystem |
| `--container NAME` | Docker container to `docker cp` the module from (`docker exec cat` corrupts the binary) |
| `--set` | Sprite set to print; default `material`; `all` prints a count per set |
| `--json` | JSON array instead of one name per line |

Exactly one of `--modl` or `--container` is required; without either the
command prints an error. Sets are `material`, `ignition`, and the
`symbol_*` sheets that draw the `ia.symbol.*` components. Sprites use
`<g class="icon" id="...">` groups, not `<symbol>`.

## Do not

- Do not invent flags; the surfaces above are complete.
- Do not treat `GenericComponent` acceptance as proof that a type string is
  valid on the gateway; only the typed inventory is verified.
- Do not use this skill to author or place components; that is the view skill.

## References

| File | Summary |
|---|---|
| `references/palette-model-map.md` | Every `ia.*` type string with its model class and source file |
