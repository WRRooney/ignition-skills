---
name: ignition-guardrails
description: Turn the Ignition write guard on or off for the current agent host (Claude Code or Hermes). The guard blocks direct writes to config/resources/** and projects/** so the ign CLI stays the only writer of gateway files. Use when the user says "guardrails on", "guardrails off", "enable the write guard", "disable the hook", "is the guard on", "let me edit view.json by hand", or asks why a shell write to a gateway file was blocked. Do not use for gateway security settings, user roles, or API token permissions.
---

# ignition-guardrails

## Usage

```bash
python3 .agents/skills/ignition-guardrails/guardrails.py on
python3 .agents/skills/ignition-guardrails/guardrails.py off
python3 .agents/skills/ignition-guardrails/guardrails.py status
```

Run from the gateway data directory (or pass `--project DIR`). Without `--host` the
script applies to every host it detects: Claude Code when `<project>/.claude/` exists,
Hermes when `$HERMES_HOME` (default `~/.hermes`) exists. `--host claude-code` or
`--host hermes` limits it to one. When the skill is installed as a Claude Code plugin,
use the path the plugin reports for this skill instead of `.agents/skills/`.

## What `on` does

| Host | Files touched |
|---|---|
| Claude Code | Copies the hook to `<project>/.claude/hooks/`; adds a `PreToolUse` entry for `Bash`, `deny` rules for `Write`/`Edit` on the two trees, and `allow` for `Bash(ign *)` to `<project>/.claude/settings.json` |
| Hermes | Copies the hook to `$HERMES_HOME/agent-hooks/`; adds a fail-closed `hooks.pre_tool_call` entry (matcher `terminal|execute_code|write_file|patch`) to `$HERMES_HOME/config.yaml`. Hermes asks for consent on the hook's first run |

`off` removes exactly those additions and the hook file. Other settings are left alone.
`status` prints `on` or `off` per host.

## Behavior of the guard

- Blocks shell redirects, `tee`, `cp`/`mv`/`rm`/`sed -i`, in-line Python writes, and
  (on Hermes) `write_file`/`patch` calls that target `config/resources/**` or
  `projects/**`. Relative paths count when the working directory is the gateway data dir;
  `$IGNITION_DATA_DIR` trees count from anywhere.
- Never blocks `git`, reads, or `ign` itself.
- Fails open on malformed input, so it cannot wedge the agent.

## When the user wants to hand-edit a gateway file

Turn the guard off, let them edit, then turn it on again. Do not work around the guard
with a different write path; that is the exact behavior it exists to stop.

## Verify

`python3 .agents/skills/ignition-guardrails/test_hook.py` exercises the hook with both
hosts' payload shapes and prints `N/N ok`.
