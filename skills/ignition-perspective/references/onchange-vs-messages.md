# A property `onChange` beats a message handler

A property `onChange` script and a page-scoped message handler that both react to
the same write run in that order, and the `onChange` finishes first. A drop
handler that reads `custom.dragging` to perform a move finds it already emptied by
a change script reacting to the same write. The drop does nothing, silently; the
only symptom is an interaction that sometimes works.

Reading the state into locals at the top of the message handler does not help.
By the time the handler runs, the clear has already happened elsewhere; ordering
inside the handler is irrelevant.

## The rule

Props holding a TRANSIENT INTERACTION (drag source, drop target, hover mode,
in-flight selection) may be bound to in order to DRAW, never watched with
`onChange` in order to REACT. Put the reaction in the message handler that owns
the interaction, and let that handler clear the state when it is done.

Use `onChange` for durable state the view owns (a selected tab, a filter) where
no message handler also reads the write.

## Declaring `onChange`

Component-level: a `propConfig` entry
`{"onChange": {"enabled": true, "script": "..."}}` on the prop path. Session-level:
`ign session-props declare --project Demo --prop-config /tmp/pc.json` with the same
entry keyed by prop path. Removing the prop with `undeclare` removes the entry too.
