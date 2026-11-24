# `ia.display.flex-repeater` behaviors

## Sizing

- `useDefaultViewHeight` and `useDefaultViewWidth` default to `true` on a
  repeater and pin every element to the repeated view's `defaultSize`. A
  variable-width element (a breadcrumb) gets clipped and later siblings render
  under the overflowing text. Set `useDefaultViewWidth: false` plus
  `elementPosition.basis: auto` for content-sized elements.
- Keep a fixed basis where a child has no intrinsic size; sparklines and SVG
  symbols collapse to 0.
- A column repeater with `useDefaultViewHeight: false` needs
  `elementPosition.basis: auto`, or every element collapses to 0 height and
  the page renders "successfully" with nothing visible.
- In a wrapping repeater, `useDefaultViewHeight: true` is the fix for the
  opposite bug: elements with no intrinsic height stretch to the container
  height and rows float mid-container. `props.style.alignContent` loses to the
  repeater's inline style; claim it from the stylesheet with `!important`.
- A wrapping column repeater in a height-bounded box produces newspaper
  columns. On a phone, set `flex-wrap: nowrap` and swap the overflow axes.

## The repeated view's root position is ignored

The repeater element is the repeated view's root `<div>`, but its `position`
comes from the repeater's `elementPosition`. A root `position.display` on the
repeated view never reaches the DOM. Only the root's `props.style.display`
(`"flex"` or `"none"`) hides the element, and only `display: none` removes it
from flex flow; a zero-width element still consumes the gap.

## Output params trickle up only into seeded keys

An output param on a repeated view writes back into the repeater's
`props.instances`, but only into a key the instance dict already carries.

1. The `instances` transform seeds the key on every instance:
   `{"tagPath": p, "isDisplayed": False}`.
2. The repeated view declares `params.isDisplayed` with
   `paramDirection: "output"` and a property binding to whatever computes it.
3. The parent reads its own repeater back with a property binding on
   `/root/<Repeater>.props.instances` and aggregates in a script transform.

This composes across hops (leaf count to row to section) and re-fires while the
form is open, which discovery-time filtering cannot do. The same rule explains
`instancePosition`: per-instance position works only when the instance dict
carries an `instancePosition` key.

## Instances from a dict

Bind `props.instances` to an expression-structure or object and finish with a
script transform that returns the sorted values of a keyed object (`idx0_x`,
`idx1_y`; keys never start with a digit, `params-and-config.md`); each instance
dict is the repeated view's params verbatim. Deep copy template objects before
returning them. A repeater with zero instances is the cleanest optional embed
(`discovery-transform-null-guard.md`).

## Layout as one object param

When a wrapper view exists to lay out a repeater, expose the repeater's layout
props as one object input param and property-bind each key onto the repeater
(`flex-sizing.md`).
