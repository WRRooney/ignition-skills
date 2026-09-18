# Expression language idioms

Applies to expression bindings, expression transforms, and `{...}` references.
Script bodies (transforms, events, library modules) are Jython, where `==` is correct.

## Operators

- Equality is a single `=`; not-equal is `!=`. `==` is a runtime parse error: the
  binding silently never evaluates while the JSON still validates. The SDK raises
  `ExpressionSyntaxError` on `==`, on unbalanced `()` or `{}`, and on an unknown
  expression function.
- `&&` and `||` are valid (single `&` and `|` also work). Do not "fix" them.
- Function names are case-insensitive (`coalesce`, `COALESCE`, `isNull`, `isnull`).
  `system.*` calls in scripts are case-sensitive.

## 8.3 replacements

| Missing in 8.3 | Use |
|----------------|-----|
| `length(s)` | `len(s)` |
| `contains(s, x)` | `indexOf(s, x) >= 0` (or `containsAny` / `containsAll` for lists) |
| `substringAfterLast(s, "/")` | `substring(s, lastIndexOf(s, "/") + 1)` |
| `join(list, ",")` | build the string in a script |
| `startsWith` | `indexOf(s, x) = 0` |
| `addDays`, `secondsBetween`, `getYear` | `dateArithmetic`, `dateDiff`, `dateExtract` |
| `randomInt()` | none; the expression language has no RNG. Sum sines with no common factor for simulated noise |

Verify any doubtful name against the 8.3 catalog (`references/api-8-3-correctness.md`).

## Bad-quality guards

- Boolean driving UI: `if(isGood({value}), {value}, false)`. Without it,
  anonymous or offline sessions overlay the component and render "null".
- Enabled flag that should default to editable: `if(isGood({value}), {value}, True)`.
- String from a tag property that may be missing:
  `if(isGood({value}) && len(coalesce({value}, "")) > 0, {value}, "auto")`.
- Any active alarm: `isGood({value}) && !isNull({value})` on
  `{tagPath}/Alarm Metrics.highestActivePriority`.
- Fallback label from a tag path: `substring({tagPath}, lastIndexOf({tagPath}, "/") + 1)`.
- Auto-hide an empty label: `isGood({this.props.text}) && len({this.props.text}) > 0`
  on the label's `position.display`.

## Preferred forms

| Use | Not |
|-----|-----|
| `!{view.custom.online}` | `{view.custom.online} = false` |
| `numberFormat(v, "#,##0.0")` | `toStr(floor(v)) + '%'` |
| `if(isGood(v), ..., "-")` early return | nested `coalesce` plus map fallbacks |
| `coalesce(v, 0) >= 75` | bare `v >= 75` (null trips the compare) |
| `lower({view.params.mode})` once into a custom prop, then `map` | repeated `if()` chains on a raw enum |
| `{x} = "alarm"` | `{x} == "alarm"` |
| `split({view.params.orientation}, '-')[0,0]` to strip a suffix | Python in a transform |
| `{view.custom.meta.type} = {this.meta.name}` (component name as variant enum) | one prop per variant |

## Expression-structure bindings

`type: expr-struct` with `waitOnAll: true` still fires its transform when a
member resolves to `null`; test each member with `is None` in the script. Use
them to hand several scalars into one script transform
(`{config: {view.custom.config}, root: {session.custom.nav.rootPath}}`) and
return a keyed object.

## Relative tag paths in tag expressions

Member expression tags may reference siblings and parents with relative paths:
`{[.]Setpoint/Value}`, `{[.]../../Value}`. Built-in substitutions `{PathToTag}`,
`{PathToParentFolder}`, `{InstanceName}` work inside UDT member expressions and
bound properties.

## References

- `{view.params.x}`, `{view.custom.x}`, `{session.custom.x}`, `{this.props.x}`,
  `{../Sibling.props.value}`, `{[.]sibling}` in tag scope, `{[default]Tanks/T01/Level}`.
- Every `{view.custom.<name>}` used anywhere must exist as a key in that view's
  `custom` block. A dangling reference resolves falsy with no Designer error, no
  overlay, and no validate finding.
- Inside a transform: `{value}`, `{quality}`, `{timestamp}` are the input.

## Style class expressions

`if({view.custom.state} = "alarm", "value flash-fast", "value")` returns a
space-separated class string. When mapping to `props.style.classes` with a map
transform, use `outputType: "style-list"`.

## Verify

Bind a label to the expression in a scratch view and render it: a parse error
(`==`, unbalanced brackets, unknown function) shows as a data-quality overlay
with the default text, not as a console error.
