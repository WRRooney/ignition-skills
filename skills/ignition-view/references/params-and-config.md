# Params, object keys, and where config lives

## Object keys never start with a digit

A property key such as `"0_pumps"` is illegal in the Designer's property editor
and, at runtime, an object carrying such keys makes the receiving view
intermittently stop reacting to param updates: a page that freezes, a dropdown
that does nothing, reload-sensitive, never reproducible headlessly, no console
error, no gateway log.

Applies to every object that crosses a view boundary: params, `custom.*`
config sections, static `items`, repeater `instances` feeds, message payloads.

Sortable keys are letters first, then the number, then the name:
`idx0_pumps`, `idx1_valves`. Sorting parses the integer in the head segment;
any `^[A-Za-z]*\d+_` head sorts the same way. Un-numbered keys are settings.

## Compound params are one object, not a JSON string or a list

A structured input is ONE object param keyed `idx<n>_<briefName>`. Never a
JSON-encoded string (defeats the Designer property editor) and never a list param
(list params re-fire unreliably). Document the legal values of an enum-ish param
in a sibling doc param, `_<name>s` holding `top,right,left,bottom`, and the shape
of a dict param in `_<name>Example`.

## Enum params: lowercase once, then map

An enum-ish param (`orientation`) is case-insensitive by construction:
`custom.orientation` <- `lower({view.params.orientation})`, and every consumer is
a `map` transform with a `fallback`, one entry per value, never a nested `if()`
chain. Visibility gates map to `true` with `fallback: false`; CSS mirrors map to
`scaleX(-1)` / `scaleY(-1)` with `fallback: ""`.

## Config and copy live in Designer-editable data, not code

Scripts discover and derive (path discovery, variant expansion, type lookups).
Descriptions, group order, per-card settings, and human-facing copy live in
`view.custom.*` objects on the page or card view, or in tag meta properties, where
a Designer user can edit them in place. The script MERGES discovered items with
declared config. Adding a card or group is then a Designer edit with no code change.
A script full of legend copy and group tables is opaque from the Designer and needs
a release to change one label.

## Input, output, and persistence

- Declare inputs `{"paramDirection": "input", "persistent": true}` in
  `propConfig` with a type-correct empty seed (`""`, `false`, `{}`), not `null`
  and not a leaked test path (`persistent-props.md`).
- Output params write back only where the parent holds a slot: a singular
  embed exposes `props.params.<name>`; a repeater needs the key seeded on every
  instance dict (`flex-repeater.md`).
- A view used inline and as a popup takes a `popup` bool param to gate its
  close affordances.
- Table column subviews receive the cell value under the param name `value`;
  a row view therefore names its instance path param `value`. Dataset cells
  holding a dict arrive as the Python `repr`; encode cells as JSON strings and
  `json.loads` in a script (`table-and-chart.md`).

## Reading params into the view

Mirror params into `custom.<name>` once (`custom.orientation` from
`lower({view.params.orientation})`, `custom.isLeftRight` from a script
`"left" in value or "right" in value`) and bind consumers to the custom prop,
never to the raw param twice. Every `{view.custom.<name>}` referenced in an
expression must appear as a key in the view's `custom` block; a dangling
reference resolves falsy with no error.

## Params vs custom

`params.*` are embed-time inputs owned by the caller; `custom.*` is state owned by
the view. A view that reads config should expose one object param with defaults
in `custom`, and property-bind each key, so callers override a subset and the
Designer edits the defaults.
