# Click targets, overlays, and pointer events on composite tiles

## Layering rules

- An alarm-frame overlay spans 102% x 102% at `top/left: -1%` with
  `zOrder: -1` so its outline draws outside the tile. Put the hover class on
  that overlay, not on the view root, where a 3px outline clips at the
  container edge.
- A value container over a graphic gets `pointerEvents: none`; each
  interactive leaf inside sets `pointerEvents: auto`. To paint above a bar
  without capturing its clicks, add `position: relative` and `zIndex: 2` to
  the container.
- A click-transparent label lives in a wrapper flex (`justify: center`,
  `overflow: visible`, `pointerEvents: none`) so the overlay behind it owns
  the click.
- Never put a click handler on a wrapper that embeds a view containing its own
  full-size click target; the two compete. Disable the wrapper's handler with
  `events.dom.onClick.enabled: false` rather than deleting it.
- An unconfigured affordance (a process flag with no target) is both invisible
  and click-transparent: bind `props.style.pointerEvents` to
  `if({view.custom.configured}, 'auto', 'none')`, and the referenced custom
  prop must exist (a dangling reference pins it to `none` forever).

## Popup opener idiom

```python
view = self.view.custom.meta.popupView
if isinstance(view, basestring) and len(view) > 0:
	tagPath = self.view.params.tagPath
	popupId = json.dumps({"params": {"tagPath": tagPath}, "view": view}, sort_keys=True)
	system.perspective.openPopup(popupId, view, params={"tagPath": tagPath},
	                             draggable=True, showCloseIcon=True)
```

The popup ID mirrors the popup's own `meta.domId` (an expression-structure of
`{view, params}` serialized with sorted keys), so a second click focuses the
same popup instead of opening another. A binding to a popup view path without
the opener is an unfinished tile. `openPopup` also accepts
`position={"width": "75%", "height": "75%"}`, `resizable`, `viewportBound`;
Escape closes a modal popup natively. A view used both inline and as a popup
takes a `popup` param to gate the close affordances.

## Shared ad hoc trend

Value readouts add a pen instead of opening a detail popup: if
`session.custom.adhocTrend` is set,
`system.perspective.sendMessage("trend-add-pen", {"tagPath": p}, scope="session")`;
otherwise open the trend popup with a fixed ID so there is one per session.
Readouts carry a generic `hover` class (`opacity .85` to `1`,
`cursor: pointer`), never button chrome.

## Fixed click contract per tile family

Label, graphic, and alarm frame open the detail popup; value readouts add a
pen. Write the contract for every family at once so tiles behave alike.

## Touch

Targets 44px; `:active` is the only feedback a phone gives, so tooltips on
footer controls are dropped in favor of a tint class.
