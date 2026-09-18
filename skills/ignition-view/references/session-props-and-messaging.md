# Session props, cross-view state, and messaging

## Session props are declared, not created

Custom session props are schema-declared per project in
`projects/<name>/com.inductiveautomation.perspective/session-props/props.json`
(`ign session-props declare`). There is no runtime API that creates one;
`system.perspective.setSessionProperty` / `getSessionProperty` do not exist in
8.3, and writing `self.session.custom.nav.selected = x` for an undeclared prop
has nowhere to land.

```json
{ "custom": { "nav": { "selectedView": "", "selectedParams": {} } }, "propConfig": {}, "props": {} }
```

Read and write in component scope only (an event handler, `onStartup`) as
`self.session.custom.nav.selectedView`. Library scripts have no `self`; have
them return values and let the component write.

- A session prop that carries a binding must be `persistent: true`;
  unpersisted session-prop bindings occasionally fail to execute. Expect the
  serialized last value to churn in `props.json` on every Designer save.
- Session-prop bindings are a last resort. A session-scoped query binding
  polls in every open session forever, open page or not; keep query bindings
  on the page and put only user choices (`scope`, `rangeHours`) in
  `session.custom`.
- `session-props` inherits per resource. A child that owns its resource must
  declare every prop the template declares (`resource-scope-and-reload.md`).
- Built-in `session.props.symbols.autoAppearance` and `autoAnimationSpeed`
  are writable from scripts and drive stock symbol looks.

## Swapping an embedded view from a nested click

A click inside an embedded view cannot change what the shell shows by writing
the shell's `view.custom.*` (the row's `self.view` is the row), and
`system.perspective.navigate` changes the page, not an embedded
`ia.display.view`'s `props.path`. The hand-off is a session prop:

1. Declare `custom.nav.selectedView` and `custom.nav.selectedParams`.
2. Nested row `onActionPerformed`:
   `self.session.custom.nav.selectedView = "Components/PumpFaceplate"` and
   `self.session.custom.nav.selectedParams = {"tagPath": self.view.params.tagPath}`.
3. Shell content area (`ia.display.view`): bind `props.path` to
   `{session.custom.nav.selectedView}` and `props.params` to
   `{session.custom.nav.selectedParams}`.

Expression bindings do not execute inside an event script, so compute the
target in Python or read a prop an expression already filled. Verify in a real
browser session; the click and `onStartup` chain does not fire headlessly.

## View state

- `system.project.requestScan()` remounts every view and wipes view-scoped
  customs. Tool pages that trigger scans keep durable UI state (`expanded`,
  `selected`) in session props, bidirectionally bound from the view's customs.
- Transient interaction state written by a script or message handler (drill
  position, hover target, handoff seed) is an unbound custom prop with
  `persistent: false`, so the Designer cannot store a preview write.
- A tag-bound custom prop may also be written by a click handler: the tag
  seeds it and the click overrides locally until the binding re-fires.

## Messaging

- A child view cannot write its parent's props across a view boundary. It
  sends a page-scoped `system.perspective.sendMessage("nav-drill", {...})` and
  the parent's root component carries a `scripts.messageHandlers` entry that
  lands it on an unbound custom prop. Binding that prop would overwrite the
  handler's write on every evaluation.
- Page-scoped messages do not queue for views not yet mounted. A consumer
  requests on `onStartup`; the producer replies and clears its copy in one
  handler script (an `onChange` on the seed prop races,
  `onchange-vs-messages.md`).
- A docked view survives same-tab navigation, which makes it the relay for
  data that must not appear in the URL. Two docks may carry the same request
  handler if each guards `if seed:` so only the dock holding a seed replies.
- Rejected: one-shot `session.custom` seeds (unbookmarkable, wrong across
  tabs, need self-clearing consumers).
