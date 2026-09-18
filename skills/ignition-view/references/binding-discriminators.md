# Binding JSON shapes: propConfig wrapper and discriminators (8.3)

Verified against gateway-written `view.json` files. Field names are exact.
Semantics and builder usage are in `bindings-and-transforms.md`; the enforced
model rules are in `model-shapes.md`.

## propConfig wrapper

Each entry is keyed by property path and wraps the binding under an inner
`binding` key. Flag-only entries are valid.

```json
"propConfig": {
  "props.text": {"binding": {"type": "tag", "config": {"tagPath": "[default]Area1/Pump01/Value"}}},
  "custom.enabled": {"binding": {"...": "..."}, "persistent": true, "access": "PROTECTED"},
  "params.tagPath": {"paramDirection": "input", "persistent": true}
}
```

Emitting `{"props.text": {"type": "tag", ...}}` without the inner `binding` key
is silently ignored. Check the view-level `propConfig` too, not only components;
a model whose view-level `propConfig` is a pass-through dict lets `"prop"` through
where the component-level union rejects it.

## Binding discriminators

| Binding `type` | Notes |
|---|---|
| `tag` | `config.mode`: `direct`, `indirect`, `expression`; `tagPath`; `fallbackDelay: 2.5`; `bidirectional` only when true |
| `property` | `config.path` (never `prop`) |
| `expr` | abbreviated; `config.expression` |
| `expr-struct` | `config.struct` dict, `config.waitOnAll` |
| `query` | `config.queryPath` (not `path`), `polling {enabled, rate}`, `parameters`, `returnFormat`, `cacheAndShare`; never raw SQL |
| `tag-history` | `config.tags` (list of `{path}` or an expression string), `dateRange`, `aggregate` (one, top level), `returnSize {type: RAW\|FIXED, numRows}`, `returnFormat Wide\|Tall\|Calculations` |
| `http` | nested `config.request {method, url, auth, headers, body}`; `connectTimeout`, `socketTimeout`, `polling` are siblings of `request` |

Every binding also carries `enabled: true` and `overlayOptOut: false`; set
`enabled: false` to disable a binding in place instead of deleting it. Polling
`rate` and `numRows` are strings (`"5"`), not numbers.

## Transforms

Transforms are an array nested under the binding, not a sibling of it; a
misplaced sibling `transforms` array is ignored and the prop shows the
untransformed value. `type` values are `map`, `format`, `script`, `expression`
(full word, unlike the `expr` binding).

```json
{"type": "map", "inputType": "scalar", "outputType": "scalar",
 "mappings": [{"input": true, "output": "ON"}], "fallback": "-"}
{"type": "format", "formatType": "datetime", "formatValue": "EEE MMM d HH:mm"}
{"type": "script", "code": "\treturn value"}
{"type": "expression", "expression": "{value} * 100"}
```

`map.inputType` may be `range` with `{min, max, exclusiveMin, exclusiveMax}`
inputs; `map.outputType` also accepts `style-list`, `color`, `expression`,
`inline-style`, `document`. Map-transform boolean gates round-trip as booleans,
not strings. In an `expression` transform `{value}` is the binding output.

## Indirect references and tag-path addressing

`references` is a flat dict of name to expression. Names are arbitrary
(`{"tagPath": "{view.params.tagPath}"}` with `tagPath: "{tagPath}/Value"`) or
numbered (`{"1": ...}` with `{1}`, what the Designer writes). A reference may
point into a nested param key (`{view.params.value.tagPath}`). Do not prepend a
provider to the template; put the qualified path in the param value.
Addressing: `.prop` on the node is a tag property (custom or built-in,
`.tooltip`, `.enabled`), `/Member` is a member tag, `/Member.engUnit` a member's
property.

## Property `onChange` script shape

Exact and silently ignored when wrong: `{"enabled": true, "script": "..."}` as a
sibling of `binding` in the propConfig entry. An event-handler envelope
(`{"config": {"script": ...}, "type": "script"}`) saves and never runs. Scope:
`self`, `currentValue`, `previousValue`, `origin`, `missedEvents`.

## Verify

Mount a scratch view with the indirect binding and one with a direct binding to
the resolved path, render both headlessly, and compare `.ia_qualityOverlay--error`
counts. If the direct probe is clean and the indirect one is not, the binding
shape is wrong, not the tag.
