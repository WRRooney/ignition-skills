# Style classes, state styling, and the stylesheet

## `variants[].pseudo` is CSS-only

`style.json` is `{"base": {"style": {...}}, "variants": [{"pseudo": "<css-pseudo>", "style": {...}}]}`.
`pseudo` accepts real CSS pseudo-classes only: `hover`, `disabled`, `first-child`,
`last-child`, `visited`. Perspective resolves it against DOM state, not bound data,
so a custom pseudo such as `"critical"` never activates.

## One class per discrete state

Define a base-only class per state (`alarm-critical`, `alarm-medium`, `alarm-low`,
`alarm-normal`) and switch by binding the component's `props.style.classes`:

```python
c.bind_expression("props.style.classes",
    'if({view.custom.priority} >= 3, "alarm-critical", if({view.custom.priority} = 2, "alarm-medium", "alarm-normal"))')
```

or a map transform with `outputType: "style-list"`. Reserve `variants` for genuine
`hover` / `disabled` styling.

Write them in bulk so a family stays consistent:

```bash
ign style-class write --project Demo --file /tmp/alarm-classes.json   # {"alarm-critical": {"base": {...}}, ...}
```

Style class placement: the topmost folder covering all consumers; a single-view
class goes in a folder named after the view. Names are lowercase-dash.

On disk a class is
`projects/<name>/com.inductiveautomation.perspective/style-classes/<path>/<Name>/style.json`
(`{"base": {"style": {...}}, "variants": [...]}` only) with a `resource.json`
of scope `G` listing `["style.json"]`. Components reference it unprefixed
(`"classes": "alarm-critical"`); only raw stylesheet selectors carry `.psc-`.
There is no REST read-back for style classes: verify by disk shape, a 2xx
`/scan/projects`, and a headless render of a view that uses the class.

## Fan-out through a custom prop

When one state drives several components, compute the class string once on
`custom.styleClasses` (expression binding) and give every consumer a plain
property binding on `view.custom.styleClasses`. One expression, N property reads,
one edit site.

## A style class can paint an SVG

A class carrying `stroke` and/or `fill` applied to an `ia.shapes.svg` paints its
child elements PROVIDED those elements declare no color of their own. Author
`elements[]` with geometry plus opacity and width only
(`{"fill": {"opacity": "1"}, "stroke": {"linejoin": "round", "opacity": "1", "width": 1}}`)
and let the class supply color; one artwork then serves every state and theme.

Prefer the module's built-in symbol variables over invented ones:
`--symbolStroke--running`, `--symbolFill--running`, `--symbolStroke--stopped`,
`--symbolFill--stopped`, `--symbolStroke--default`, `--pipeStroke`,
`--pipePrimaryFill`. They are defined nowhere on disk (not in any theme
`variables.css`); they ship inside the Perspective module, so hand-drawn geometry
tracks the stock `ia.symbol.*` palette in every theme. Write `var(--symbolStroke--default)`;
a bare `--symbolStroke--default` is a silent no-op.

`opacity` is not a state channel: dimming a stopped state also mutes the stroke
and muddies a high-performance palette. Read state purely by color.

## The project stylesheet

`projects/<name>/com.inductiveautomation.perspective/stylesheet/stylesheet.css`,
written with `ign stylesheet upsert --marker <block> --file <css>`. Selectors
target style classes with the `.psc-<class>` prefix; view JSON references the
class unprefixed in `style.classes`, and the runtime adds the prefix. This is the
only channel for `@keyframes` and CSS variables driving animation, because
`ia.display.markdown` strips `<style>` and `<script>`. Rename a block by upserting
the new marker and removing the old one.

## Chart colors

`ia.chart.*` draws on a canvas and cannot resolve a CSS variable; those colors
must be literal hex (see `table-and-chart.md`). Everything else stays on theme tokens.
