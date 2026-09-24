# ignition-skills

Agent skills for building **Inductive Automation Ignition 8.3** projects with AI coding
agents: Claude Code, Codex, Gemini CLI, Cursor, OpenCode, Hermes Agent, or anything that reads the
[Agent Skills](https://agentskills.io) `SKILL.md` format.

The skills teach an agent to author tags, UDTs, Perspective views and other project
resources through the [ignition-gen-sdk](https://github.com/WRRooney/ignition-gen-sdk) `ign` CLI,
to call the gateway HTTP API without leaking the token, to inspect gateway config, and to
grow project-specific knowledge in the user's own repo instead of in the plugin.

## What you get

| Skill | Covers |
|---|---|
| `ignition-setup` | Install `ign`, configure `.env`, verify the gateway, the rules every other skill assumes |
| `ignition-tag` | Tags, UDT types and instances, alarms, `ign tag push/import/udt-*` |
| `ignition-view` | Perspective views, bindings, transforms, pages, session props, scripts, style classes, themes, runtime validation |
| `ignition-provider` | Tag provider CRUD and the resources/projects API rules |
| `ignition-db` | Database connections, alarm journals, JDBC drivers, password handling |
| `ignition-api` | Raw `/data/api/v1/*` calls with `ign api`, the OpenAPI spec, gateway logs |
| `ignition-component` | The `ia.*` component inventory and valid icon glyphs |
| `ignition-manifest` | Push manifests and `ign diff` for idempotent writes |
| `ignition-disk` | Read-only inspection of `config/resources/` and `projects/`, scans |
| `skill-learn` | Snapshot, let the user hand-edit, diff, and fold what changed into the local skill |

Each skill is a short `SKILL.md` plus `references/*.md` the agent loads only when needed.
`docs/design/lessons.md` records the implementation strategies behind the skills.

## Install

Requires the SDK first: `uv tool install git+https://github.com/WRRooney/ignition-gen-sdk` (or `pip install git+https://github.com/WRRooney/ignition-gen-sdk`).

**Claude Code (plugin)**

```
/plugin marketplace add WRRooney/ignition-skills
/plugin install ignition@ignition-skills
```

or for a checkout: `claude --plugin-dir /path/to/ignition-skills`.

**Any host, into a project**

```bash
./install.sh --host claude-code --project /path/to/gateway-data --hook
./install.sh --host codex     --project /path/to/gateway-data
./install.sh --host gemini    --project /path/to/gateway-data
./install.sh --host cursor    --project /path/to/gateway-data
./install.sh --host opencode  --project /path/to/gateway-data
./install.sh --host hermes    --project /path/to/gateway-data --hook
```

The installer copies the skills to `<project>/.agents/skills/` and symlinks them into the
host's skills directory (`--dir` overrides it). It also creates an empty
`.agents/skills/ignition-local/`, the one place project-specific rules accumulate. Hosts
other than Claude Code get a snippet to append to `AGENTS.md`/`GEMINI.md`/Cursor rules;
see `hosts/`.

**Hermes Agent**

Hermes discovers `<project>/.agents/skills/` on its own, so `--host hermes` installs there without
symlinks; project skills stay unloaded until you run `hermes skills trust` once inside the project.
Two other ways to use the skills with Hermes, without a project install:

```bash
hermes skills tap add WRRooney/ignition-skills   # browse/install from this repo as a tap
```

or add a checkout's `skills/` to `skills.external_dirs` in `~/.hermes/config.yaml`. Either way,
`ignition-setup` creates `.agents/skills/ignition-local/` in the data dir on first use.

## Guard rails (opt in)

`--hook` for Claude Code copies a PreToolUse hook that blocks shell writes to
`config/resources/**` and `projects/**`, and `hosts/claude-code/settings.example.json`
adds matching `deny` rules for the Write/Edit tools. Together they make `ign` the only
writer of gateway files.

`--hook` for Hermes copies the same script to `$HERMES_HOME/agent-hooks/` (default
`~/.hermes/agent-hooks/`); merge `hosts/hermes/config.example.yaml` into
`~/.hermes/config.yaml`. It runs as a fail-closed `pre_tool_call` hook on `terminal`,
`execute_code`, `write_file` and `patch`. Hermes hooks are global, so the script guards relative
`config/resources/` and `projects/` only when the session's cwd is the gateway data dir (or a
workspace with `.agents/skills/ignition-setup/` or `IGNITION_*` in `.env`), and
`$IGNITION_DATA_DIR`'s trees from anywhere. Other hosts get the rule as text only.

## How the skills evolve

The plugin never modifies itself. When the agent learns something about a particular
gateway, it appends to `.agents/skills/ignition-local/`. `skill-learn` turns the user's
hand-edits to generated work into rules there. Contributions of generic lessons come back
here as pull requests against `skills/*/references/`.

## Layout

```
skills/<name>/SKILL.md            the skill (frontmatter: name, description)
skills/<name>/references/*.md     lazy-loaded detail
hosts/<host>/                     per-host adapters (hook, settings, snippets)
install.sh                        per-host installer
docs/design/lessons.md            strategies and best practices behind the skills
.claude-plugin/                   Claude Code plugin + marketplace manifests
```

## License

Apache-2.0.
