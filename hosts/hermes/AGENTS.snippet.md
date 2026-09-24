<!-- Append to the project's AGENTS.md (or .hermes.md if it has one: Hermes loads only the first found) -->
## Ignition

Skills for this gateway live in `.agents/skills/` (installed by ignition-skills; run
`hermes skills trust` once in this directory so Hermes loads them). Read
`.agents/skills/ignition-setup/SKILL.md` first. All writes to `config/resources/**` and
`projects/**` go through the `ign` CLI; never edit those JSON files directly, and never
call the gateway with curl (the token would land in argv). Project-specific learnings go in
`.agents/skills/ignition-local/`.
