# `ia.symbol.*` components

## Valve orientation is `props.valve`

`ia.symbol.valve` has no `orientation` prop. Its body direction is `props.valve`
with values `top | bottom | left | right` (where the actuator points; `top` and
`bottom` give a horizontal pipe). The pump, motor, sensor, and vessel symbols use
`props.orientation`; a binding on `props.orientation` for a valve parses, shows no
error, and does nothing. Bind `props.valve` on every valve leaf, and treat a
`props.orientation` binding on a valve as dead code.

Other valve props: `appearance`, `state`
(`open | closed | failedToOpen | failedToClose | partiallyClosed | default`),
`reverseFlow`, `label` and `value` sub-objects.

## A blank valve on a cold session is a client race

Signature: `[data-component="ia.symbol.valve"] svg` has inline `visibility:hidden`
and zero child shapes; the component box is sized normally; no console or
gateway error; it never recovers (scroll, resize, waiting). The symbol requests
its SVG layers from the client's symbol renderer store; when the appearance
library is not yet in `sessionStorage`, later requesters subscribe and wait, and
some subscribers are never notified when this coincides with the session's initial
burst (the material icon library lands at the same moment). The layers do end up
stored; the component simply never re-requests. Cold sessions fail most of the
time, warm sessions sometimes, `ia.symbol.motor` never.

View-level gates do not fix it: a timer expression, a tag-quality proxy, display
gates, sizing tricks, `useDefaultView*` all evaluate on the gateway and land
before the cold client paints. Do not "fix" it in views; several unrelated changes
have each appeared to fix it by timing coincidence.

What to do:

- `ign view validate` reports `symbol_svg_empty` (count of empty hidden
  `ia.symbol.*` svgs) as a warning, not a failure. Treat a blank symbol in a
  headless render as this race unless the DOM shows a non-empty svg.
- Warm the session (visit another symbol page first) to reduce noise.
- Untried real fixes: a session-level `custom.symbolsReady` set a few seconds
  after session startup gating valve leaves; or a vendor bug report.

## Symbol artwork vs icons

The `symbol_simple`, `symbol_p&id`, and `symbol_mimic` sprite sheets are the
artwork behind `ia.symbol.*`, addressed by the components, not by an icon path.
`ia.display.icon` uses the `material` and `ignition` sets (see `icons.md`).
