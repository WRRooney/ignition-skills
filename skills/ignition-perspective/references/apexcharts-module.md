# ApexCharts Perspective module (`embr.chart.apex-charts`) gotchas

Third-party chart component. Every failure below blanks the chart with only a
browser console error, so `ign view validate` reports it as a console warning,
not a crash. Built-in `ia.chart.*` gotchas are in `table-and-chart.md`.

## Formatter strings

Formatter strings are evaluated client-side. The safe syntax everywhere is a
parenthesized block arrow: `"(value) => {\n  return ...;\n}"`. The concise form
`"val => ..."` works at `tooltip.y[].formatter`, `title.formatter`, and
`legend.tooltipHoverFormatter` but crashes chart creation at
`yaxis.labels.formatter` (`TypeError: ke is not a function`). When a chart
blanks, suspect a formatter string first.

## Per-series option arrays

- Arrays such as `yaxis: [...]`, `tooltip.y: [...]`, `tooltip.enabledOnSeries`,
  and `stroke.curve: [...]` must never outnumber the series present. A mismatch
  crashes create or update (`undefined (reading 'group')`,
  `null (reading 'length')`). Pin the count with a static `props.series`
  skeleton carrying the same names and order the series binding emits; the
  skeleton is load-bearing.
- Do not drive `props.options.*` through bindings that update alongside the
  series binding; rapid `updateOptions` churn crashes internals. For
  mode-switching charts use two fully static chart components display-switched
  with `position.display`.
- Map multi-y-axis entries by index (`yaxis[i]` to `series[i]`), not by
  `seriesName`; name matching mis-assigns axes when hidden duplicate axes are
  present. Still give series human names for legends.
- Fake stacked panels in one chart by giving each lane its own y-axis and
  scaling bands apart (`-0.1..2.5` for a state lane, `-120..100` for a position
  lane, negative labels hidden by the formatter).
- Tooltips: one object-form `tooltip.y` whose formatter branches on
  `opts.seriesIndex`; arrays of per-series formatter strings render only the
  timestamp. Row visibility via `tooltip.enabledOnSeries`.
- Axis tick labels appear only on values ticks land on; pick `min`, `max`, and
  `tickAmount` so wanted values (0, 1) land exactly, and match with a small
  tolerance in the formatter.

## Boolean state trend

Three series: a gray `combined` stepline with every point (keeps vertical
transitions continuous) plus green and red overlays split per state with null
breaks; y-axis padded `min: -0.1, max: 1.1` so the line is not clipped;
`legend.show: false`. Data from `system.historian.queryRawPoints` on a
30-second refresh.
