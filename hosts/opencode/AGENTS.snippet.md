<!-- Append to the project's AGENTS.md -->
## Ignition

Skills for this gateway live in `.agents/skills/` (installed by ignition-skills). Read only the skill the task needs:

| Task | Skill |
|---|---|
| Install `ign`, `.env`, API token, connection errors | `ignition-setup` |
| Tags, UDT types and instances, tag values, tag alarms | `ignition-tag` |
| Tag providers | `ignition-provider` |
| Database connections, alarm journals, JDBC drivers | `ignition-db` |
| Perspective views, pages, styles, themes, component types, icons | `ignition-perspective` |
| Project library scripts, gateway and session event scripts | `ignition-scripts` |
| Named queries | `ignition-queries` |
| OPC UA devices, including simulators | `ignition-device` |
| Any other gateway endpoint, logs, alarm pipelines | `ignition-api` |
| Reading gateway files, config layers, scans | `ignition-disk` |
| What changed since the last push (`ign diff`) | `ignition-manifest` |

These skills and `ign` need the gateway's `/data/api/v1` API. If `gateway-info` returns 404,
the gateway is too old: stop and tell the user. All writes to `config/resources/**` and `projects/**` go through the `ign` CLI; never
edit those JSON files directly, and never call the gateway with curl (the token would land
in argv). If no `ign` verb covers a task, stop and report what is missing; do not modify
`ignition-gen-sdk` unless the user asks. Project-specific learnings go in
`.agents/skills/ignition-local/`.
