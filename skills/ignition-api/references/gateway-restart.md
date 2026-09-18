# Restart the gateway over REST, and what `pending: []` means

```
ign api POST '/data/api/v1/restart-tasks/restart?confirm=true' --confirm
ign api GET /data/api/v1/restart-tasks/pending
```

The first restarts the gateway (no container access needed). The second lists
restart tasks the web UI has queued.

## Wrong

- Reading `{"pending": []}` as "no restart needed". Changes made by writing
  files and scanning never enqueue a restart task, so the tracker knows nothing
  about them.
- Restarting to make a view, page, tag, or Perspective-scope library script
  change take effect. A project scan loads all of those; if the change did not
  show, the resource is malformed or the log has an error
  (`gateway-logs.md`).
- Restarting a shared gateway without asking. It drops every Perspective
  session and interrupts MQTT and OPC connections for about a minute.

## Right

Restart only for state the running gateway caches independently of disk:

- the resource model built from an old `resource.json` (a removed
  `thumbnail.png` entry that keeps logging `NoSuchFileException`);
- a project record damaged by a destructive `PUT /projects/{name}` and since
  restored on disk (`put-projects-full-replace.md`);
- a gateway-scope (tag event, timer, pipeline) script that does not hot-reload.

Get the operator's consent first, and say what will be interrupted.

## Verify

`ign logs --search WebServerManager` shows the boot sequence after a restart;
the errors you expected to clear should not reappear on the next
`ign api POST /data/api/v1/scan/projects --confirm`.
