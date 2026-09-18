# Persistent props and seed values

Three kinds of stored value sit in `view.json`, and each needs different handling.

## Bound props: the stored value is a volatile snapshot

A persistent BOUND prop's serialized value is the Designer's last snapshot. It
flips between null, live values, and even mojibake across Designer saves. Never
hand-maintain it, never read meaning into it in a diff, never "fix" it; the binding
overwrites it on mount. Also, when a binding drives a prop, do not leave a static
value for the same prop in the component tree (a stale shadow).

## Unbound persistent props: the stored value is live config

An UNBOUND `persistent: true` prop's value is exactly what every mount starts with.
The Designer writes back the CURRENT runtime value on save, including whatever a
message handler or event script wrote during preview mode. A prop designed to
start empty can therefore ship non-empty, and nothing in the diff looks wrong.
Input params leak the same way: a test path typed into a param during a Designer
session ships as its default.

- After a Designer session, diff unbound persistent seeds on purpose and reset the
  ones that must start empty.
- The durable fix for transient interaction state (drill position, hover target,
  a handoff seed) is `persistent: false`; the Designer never stores a
  non-persistent prop, so it cannot be seeded by accident. Reserve
  `persistent: true` for config a human sets in the Designer.
- `ign view set-prop --project Demo --view-path Pages/Overview --prop custom.selected --no-persistent`
  drops the stored seed and sets the flag in one call.

## Bound gate props: keep the undecided sentinel

A bound prop that gates rendering or encodes an authorization verdict IS read
between mount and the moment its binding resolves. If the stored value is a
decided one (a Designer save persisted `1` where `-1` meant "undecided"), every
mount routes to the protected view until the script transform finishes; that is a
flash of protected content, and a script transform is the slowest tier. Persist
the undecided sentinel, never a decided value, and audit gate props after every
Designer sweep. A `-1 -> 1` diff on a gate prop is a security regression that
looks like snapshot noise.

Same family, lower stakes: never persist `ia.container.breakpt` `currentBreakpoint`;
the Designer saves whichever branch was previewed and can pin the first paint to
the wrong one.

## Null seeds are banned on unbound scalars

A `custom` or `params` value seeded `null` carries no datatype: format
transforms and numeric expressions blank out or error, and the Designer canvas
renders empty. Seed every unbound scalar:

- numbers: a real mid-band value (`50`, `0.5`), not `0`, not an extreme;
- strings: `""`;
- `tagPath`: a live tag on the gateway so the view previews against real data.

## Dangling references

Every `{view.custom.<name>}` in a binding must be a key in the view's `custom`
block. A missing one resolves falsy silently: no Designer error, no runtime overlay,
no `ign view validate` finding. A `pointerEvents` binding on an undeclared prop pins
the component to `none` forever.
