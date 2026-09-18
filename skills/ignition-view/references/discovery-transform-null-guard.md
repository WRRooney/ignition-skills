# Transforms fire with null: guard before any browse or query

A binding's script transform runs on first mount with whatever the source
resolved to at that moment: `null` for an indirect tag reference whose `{tagPath}`
is still `""`, `null` for an expression-structure member that has not resolved.
`waitOnAll: true` does not shield you; null counts as a value, so the structure
fires once every member has *a* value.

An empty path handed to `system.tag.browse`, `system.tag.query`, or
`system.tag.getConfiguration` is the PROVIDER ROOT. A recursive
`getConfiguration("")` walks the entire provider, once per consumer, on every
mount. There is no error; the symptom is a form that takes seconds to load.

## The rule

The first line of every transform that feeds a browse, query, or configuration
read (directly or through a library function):

```python
# plain property or tag binding
if value is None or value == '':
	return []

# expression structure
if value.folderPath is None or value.layout is None:
	return []
if value.folderPath == '':
	return []
```

Return `[]` so a repeater renders nothing. Do not hide the component instead: a
hidden embed still mounts and still discovers.

## The embed-level half

Gate an optional embedded view on `props.path`, not `position.display`. An
`ia.display.view` with an empty path logs a `React.cloneElement(null)` console
error, so an optional embed is better modeled as a flex repeater with zero
instances than as a hidden view.

## Library side

Library discovery functions accept the same guard as a defensive second line,
but the view-side guard is the one that prevents the walk; the library cannot know
whether `""` was intentional.
