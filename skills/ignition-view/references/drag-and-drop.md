# Drag and drop in Perspective 8.3

## Native drag events never fire

`events.dom` lists `onDragStart`, `onDrag`, `onDragOver`, `onDragEnter`,
`onDragLeave`, `onDragEnd`, and `onDrop`. That is React's synthetic event list,
not a promise: nothing in the client sets `draggable="true"` on any element, so
the browser never starts a drag and none of those handlers run. A real
browser-level drag produces only `mouseenter`, which proves the wiring is fine and
the negative is real.

## Simulate it with mouse events

These fire, in this order:

| Event | Fires on | Use |
|-------|----------|-----|
| `onMouseDown` | the source row | pick up: stash the path in a view custom prop |
| `onMouseEnter` | any row while the button is held | track the hover target, draw the drop indicator |
| `onMouseUp` | the row under the cursor | drop: commit the move, clear the drag state |

`onPointerDown` / `onPointerUp` are listed but do not fire; use the mouse variants.

## Ordering traps in the same feature

- A click is `mousedown` plus `mouseup` on one row and is indistinguishable from
  a drag unless the cursor must reach a DIFFERENT row first.
- `onMouseDown` on a row also fires for a chevron inside it, so expanding a node
  starts a drag, and the re-render slides a new row under the cursor before release.
- Keep the drag state on a `persistent: false` prop; the Designer otherwise saves
  a mid-drag value as the seed (`persistent-props.md`).
- Never put an `onChange` on the drag-state prop; the message handler that
  performs the drop reads it after the change script has already cleared it
  (`onchange-vs-messages.md`).

## `ia.display.tree` cannot host any of this

The tree component has no events; its props reducer reads only `selection` and
`selectionData`. Row menus, inline buttons, and drag require a hand-built tree from
flex repeaters.
