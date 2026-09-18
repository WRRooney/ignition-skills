# Page routing, URL params, docks, and popups (8.3)

## URL params

- A mount is split on `/`; `:name` segments are params; a URL with more
  segments than the mount is rejected. `*`, `**`, and `:p*` are matched as
  literal text. There is no catch-all or multi-segment param.
- To carry a nested path in one param, percent-encode the whole thing as one
  segment: `/App/Area1%2FPump01%2FPage`. The split happens before decoding,
  so `%2F` never becomes a boundary and the param arrives decoded.
- Encode with `urllib.quote(s, safe='')`. The expression `urlEncode()` is
  form-urlencoded and emits `+` for spaces, which survives decoding and
  corrupts labels.
- Mount precedence: fewer segments first, then more literal segments. `/App`
  and `/App/:x` coexist; a second two-segment `/App/:y` shadows.
- A slash-separated guess at a nested URL returns "View Not Found", which
  looks like a broken view but is a malformed URL.

## Page params reach only the primary view

Page URL params land on the primary view as its own `params` (declared
`paramDirection: input`, `persistent: true`). There is no `page.props.params`.
A docked view reads `{page.props.path}` (the raw, still encoded pathname) and
decodes it itself.

## `page.custom` does not exist

The page scripting object exposes no property trees; `self.page.custom` is
`None` and writes raise or no-op. Do not design around it.

## Dynamic tab title

There is no `system.perspective` title setter, but a view may assign
`self.page.props.title = value` inside a script transform (for example bound on
a `custom.label` property). The mount's static title is the fallback before the
binding fires; without either, the tab reads the project name.

## Docks

- One dock per side. A page config may declare several docks on one side but
  only the active one lays out; the rest mount at 0 x 0. Stack chrome as rows
  inside one docked view. The other sides are free (`sharedDocks.bottom`).
- Dock height is not CSS-authored: the client writes it inline on
  `.docked-view-<side>` from the page-config `size` and derives `.center`
  margins from it. Changing height per breakpoint means overriding both the
  dock and `.center` from the stylesheet.
- In a headless probe, `getComputedStyle` after a synchronous style write
  returns the stale value; await a tick before measuring.
- Page-config inherits per resource; mount routes in the template project and
  check for an owned copy in children after any Designer session
  (`resource-scope-and-reload.md`).

## Popups

`system.perspective.openPopup` accepts `position={"width": "75%", "height": "75%"}`
(viewport percent strings), `resizable`, `viewportBound`, `draggable`,
`showCloseIcon`. Escape closes a modal popup natively. The Designer's built-in
popup action serializes as
`{"type": "popup", "scope": "C", "config": {"type": "open", "viewPath": ..., "viewParams": ...}}`;
the SDK's `PopupEventHandler` emits it, and an unmodeled handler type rejects
the whole view on load. The opener idiom is in `click-layering.md`.
