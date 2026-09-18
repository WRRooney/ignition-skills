# Component prop and event quirks (8.3)

Verified live; each one fails silently when wrong.

## Unknown props are kept and ignored

Perspective does not reject a prop it does not recognize. A wrong key sits in
`props`, the real prop stays at its default, and nothing logs. Every Perspective
prop key is camelCase; a key containing `_` is almost always a mistake
(`align_vertical` for `alignVertical`, `read_only` for `readOnly`, `show_legend`
for `showLegend`). Copy the key from a Designer export or `ign component list`.
The SDK's props models allow extra keys (so unmodeled real props pass) but raise
on an underscore key whose camelCase form is a known field. Sweep a project with
a grep for `_` keys under `props`.

## Type strings and prop names

- Numeric input is `ia.input.numeric-entry-field`; `ia.input.numericEntry`
  does not exist.
- Text inputs' placeholder prop is `placeholder`, not `placeholderText`.
- Radio group takes `radios: [{text, value}]` plus `orientation`, not `options`.
- `ia.symbol.valve` has no `orientation` prop; body direction is `props.valve`
  (`symbols.md`). Other `ia.symbol.*` use `props.orientation`. Symbols share
  `appearance` (`simple|p&id|mimic|auto`), `state`, `animated`, and label/value
  sub-objects with `location: "hidden"`. State enums: motor/pump
  `default|running|stopped|faulted`; valve
  `default|open|closed|partiallyClosed|failedToOpen|failedToClose`.
- Embedded view drop config: `props.dropConfig.udts = [{"action": "path",
  "param": "tagPath", "type": "Pump"}]` lets a tag-browser drag of that UDT
  type embed the view with `tagPath` set.
- `ia.display.markdown`: content is `props.source`; `props.markdown` is a
  render-options object (`model-shapes.md`).

## `ia.display.label`

- `textOverflow: ellipsis` in `props.style` is inert: the text lives in an
  inner div and the style lands on the wrapper. Ellipsis needs the stylesheet:
  `.psc-<class> .ia_labelComponent > div {overflow: hidden; text-overflow: ellipsis; white-space: nowrap}`.
- The label writes its own inline color, which a container class cannot
  cascade past; bind color and weight or target it from the stylesheet.
- `textStyle: {textAlign: center, whiteSpace: pre-wrap}` centers and wraps
  only on explicit newlines.

## Events

- `ia.input.text-field` has no `component.onActionPerformed`; declaring one
  saves and is ignored. Use `events.dom.onKeyDown` with
  `if event.key != "Enter": return`. Dropdowns and buttons do have
  `onActionPerformed`.
- `events.dom.onClick.enabled: false` disables a handler in place.
- A popup event handler cannot be made conditional; gate it with a separate
  absolutely positioned child shown only when the condition holds.
- Text-input `onChange` is the last resort; guard `if origin != "Browser": return`.

## Layout and style

- Flex containers accept `props.style.gap: "5px"`.
- Color props take the bare token (`"--neutral-90"`); `var()` only in CSS.
- `props.style.zoom` passes through and rescales the px unit (geometry and
  fonts); `getBoundingClientRect` already returns zoomed coordinates.
- `page.props.dimensions.viewport.{width,height}` exist and update live;
  viewport height includes docked chrome.
- Centering one item between two variable blocks in a docked row: take it out
  of flow (`position: absolute; left: 50%; transform: translateX(-50%)`) with
  an explicit width. When only one side varies, a `grow: 1` middle with
  `justify: center` is enough.
- An `ia.container.flex` default computes to `overflow: auto`, so a too-short
  header scrolls; strip the overflow or size the box.
- Dropdown option overlays render in a portal (`.ia_dropdown__optionsModal`,
  `.iaDropdownCommon_option`, modifiers `--focused` / `--selected`); style them
  from the project stylesheet, not a style class.
- Sparkline internals (`.ia_sparklineComponent__{line,firstMarker,lastMarker,highMarker,lowMarker}`)
  default to green, red, and purple; override from the stylesheet.

## Verify

Render headlessly (`ign view validate`): a mis-keyed prop shows as the default
rendering with zero console errors; a missing embed param shows as
`.ia_qualityOverlay--error` on every bound prop inside the embed.
