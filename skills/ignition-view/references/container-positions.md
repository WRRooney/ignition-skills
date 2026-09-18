# Container child positions, tabs, and breakpoint containers

Each container type gives its children a different `position` object. All of
these were confirmed against Designer-exported views; the SDK's position models
(`FlexChildPosition`, `CoordinatePosition`, `ColumnBreakpoint`, ...) enforce them.

| Container type | Child `position` keys |
|---|---|
| `ia.container.flex` | `basis`, `shrink`, `grow`, `display` |
| `ia.container.coord` | `x`, `y`, `width`, `height`, `rotate: { anchor }` |
| `ia.container.split` | `position`: `left`, `right`, `top`, or `bottom` |
| `ia.container.tab` | `tabIndex` |
| `ia.container.breakpt` | `size`: `large` or `small` (small may omit position) |
| `ia.container.column` | `breakpoints: [ { colIndex, name, order, rowIndex, span } ]`, plus `height` |

- Tab children are a flat sibling list keyed by `position.tabIndex`; they are
  not nested under a tab entry.
- Column breakpoint `name` is usually `sm`, `md`, or `lg`, but custom names are
  allowed; the model types it as `str`.
- `rotate` is observed as `{ "anchor": "50% 50%" }`; `angle` is a real key but
  rarely exported, so it stays an open dict.

## Tab `props.tabs` has two valid forms

String array: `"tabs": ["Overview", "Trends"]`. Object array (what the Designer
writes; supports per-tab disable and icon):

```json
"tabs": [ { "text": "Overview", "disabled": false },
          { "text": "Trends", "disabled": true, "icon": { "path": "material/timeline" } } ]
```

`disabled` is always present in the object form, even when false. The builder
takes `tabs=["Run"]` or `tabs=[TabSpec(text="Run", disabled=True)]`.

## `ia.container.breakpt`

- The type string is `breakpt`; `ia.container.breakpoint` does not exist.
- Props: `breakpoint` (px, default 640), `determinant` (`width` or `height`),
  `currentBreakpoint` (written by the container; never persist a value for it,
  the Designer stores whichever branch was last previewed).
- Renders exactly one child and supports at most two; a third is inert.
  Children are designated by `position.size`; omitted means small. A three-way
  split nests two containers.
- The non-matching branch is not mounted and its bindings do not run, which is
  the opposite of `position.display`. A breakpoint router therefore beats CSS
  hiding for form-factor headers: repeaters and clock expressions in the desktop
  branch do not evaluate at phone width.

## Embed hygiene on `ia.display.view`

- Do not set `useDefaultViewHeight` or `useDefaultViewWidth` to `false`
  explicitly; omit them and set `true` only when the embed should show the view
  at its own `defaultSize`. Tab and panel content embeds carry neither, so the
  body fills the tab.
- Add `overflow: visible` on containers hosting bars, absolute overlays, or
  shadows.
- A singular embed needs no seeding for output params: the parent reads
  `{.../<Embed>.props.params.<name>}` directly. Repeaters differ
  (`flex-repeater.md`).
- `View 'X' restarted but missing from session.` on a short-lived headless
  session is a teardown race, not a defect.

## Verify

Strict child-position models plus a test that walks every on-disk view,
collects `position` keys per container type, and asserts they are all modeled.
Add new keys from the corpus, not from memory.
