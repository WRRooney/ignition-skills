# Flex sizing and layout rules

## Spacing

Flex containers accept `props.style.gap: "8px"` (any CSS length). Prefer it over
per-child margins when sibling spacing is uniform.

## Rules that bite

- Value plus unit row: the value gets `grow: 1`, the unit gets `shrink: 0`, so
  the unit is never squeezed.
- A column-direction flex repeater with `useDefaultViewHeight: false` needs
  `elementPosition.basis: "auto"`, or every element collapses to zero height. The
  page renders "successfully" at zero height with no error anywhere.
- `defaultSize` is both the Designer preview canvas and the embed fallback size.
  Size it to the real use (a tile placed at 338px tall should not declare 160).
- A root flex `font` and `gap` on the root are the cheapest way to give a family
  of leaf views one rhythm.

## `position.display` vs `style.display`

`position.display` takes a boolean. `style.display` takes a CSS string
(`"none"`, `"unset"`). Gate a component with `position.display` bound to a
boolean. Only when forced into a style object (a `style` param, a component with
no `position`) use the strings. Mixing them fails silently: a raw bool in
`style.display` never hides anything.

## Do not emit Perspective defaults

Emit only what differs from the default: no `props.direction: "row"` on
`ia.container.flex` when it is the default, no `position.basis: "auto"`,
`position.grow: 0`, `props.params: {}` on an embed, or `props.style.overflow: "auto"`
on a column that never scrolls. A default in the file is churn on the next
Designer save and hides the one prop that matters.

## Repeater layout as one object param

When a wrapper view exists to lay out a repeater, expose the repeater's layout as
ONE object param (`layout`) and property-bind each key onto the repeater prop of
the same name: `direction, wrap, justify, alignItems, alignContent,
elementPosition, elementStyle, style`. Callers override a subset, the Designer
edits the defaults, and there is no per-prop param sprawl.

## Breakpoint containers and repeaters

A breakpoint container mounts only the matching branch; do not persist
`currentBreakpoint` (`container-positions.md`, `persistent-props.md`). Repeater
element sizing, the ignored root position, and output-param write-back are in
`flex-repeater.md`; embed `useDefaultView*` hygiene in `container-positions.md`.
