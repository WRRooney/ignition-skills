# `ia.shapes.svg` graphics: stretchable runs, orientation, animation

The color rules (colorless geometry painted by a style class, the module's
`--symbol*` and `--pipe*` variables) are in `style-class-state-binding.md`.
This file covers geometry, orientation, animation, and sizing.

## Stretchable runs and orientation

- `preserveAspectRatio: "none"` lets one fixed path draw a segment of any
  length; put the SVG in a percent-mode `ia.container.coord` root with every
  child at `position: {height: 1, width: 1}` so layers stack full-bleed.
- Four directions need two SVGs (one per axis, same `d`, different `viewBox`),
  gated by `meta.visible` from `lower(orientation)` plus a map transform, and
  mirrored with `props.style.transform` `scaleX(-1)` or `scaleY(-1)`.
- When the flow axis is vertical the tile becomes a row with label and state
  beside the graphic; `-reverse` suffixes pick the other side, and the leaf
  never sees the suffix (`split({view.params.orientation}, '-')[0,0]`).
- A label riding on a segment is a third full-bleed flex layer with percent
  padding so it stays clear of the arrow point at any length.
- A flag or symbol occluding a pipe fills with the canvas background variable,
  not `transparent`.

## Pipe classes

Pipe classes are complete, mutually exclusive stroke/fill pairs (`pipe`,
`pipe-active`, `pipe-inactive`); nothing dashes or dims. Opacity is not a state
channel because it also mutes the stroke.

## Animation

- SMIL `<animate>` children inside the SVG elements work; bind each `dur` to a
  custom prop such as `400 / {session.props.symbols.autoAnimationSpeed}`
  seconds while running and a huge value (`999999s`) when stopped. No
  stylesheet entry needed.
- Alternatively, keyframes live in the project stylesheet
  (`@keyframes keyframes--spinY` plus `.psc-animation--spinY`) and a map
  binding on `props.style.classes` swaps `animation--spinY` in and out. The
  stylesheet is the only channel for `@keyframes`; `ia.display.markdown`
  strips `<style>`.
- A map transform onto `props.elements[0].fill.paint` uses
  `outputType: "color"`. Map-transform boolean gates round-trip as booleans,
  not strings.

## Sizing symbols in cards

An SVG or symbol has no intrinsic width; a centered column flex collapses it
to 0. Give it a px basis with `grow: 1`, or embed the view at its own
`defaultSize`; a percent height is 0 at first layout inside an auto-height
repeater element (`flex-repeater.md`).
