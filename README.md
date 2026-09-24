# ignition-skills

Agent skills for building **Inductive Automation Ignition 8.3** projects with AI coding
agents: Claude Code, Codex, Gemini CLI, Cursor, OpenCode, Hermes Agent, or anything that
reads the [Agent Skills](https://agentskills.io) `SKILL.md` format.

The skills drive the [ignition-gen-sdk](https://github.com/WRRooney/ignition-gen-sdk)
`ign` CLI: author tags, UDTs, Perspective views and other project resources as typed
Python, call the gateway API safely, inspect gateway config, and keep project-specific
knowledge in your own repo.

## Quick start

1. Install the SDK:

   ```bash
   uv tool install git+https://github.com/WRRooney/ignition-gen-sdk
   ```

2. Install the skills for your agent (see below).
3. In your gateway data directory, ask the agent to set up `ign`. The `ignition-setup`
   skill walks it through `.env`, the API token, and a first connection.

## Install

**Claude Code**

```
/plugin marketplace add WRRooney/ignition-skills
/plugin install ignition@ignition-skills
```

For a local checkout: `claude --plugin-dir /path/to/ignition-skills`.

**Hermes Agent**

```bash
hermes skills tap add WRRooney/ignition-skills
```

**Any host, into a project**

```bash
git clone https://github.com/WRRooney/ignition-skills
cd ignition-skills
./install.sh --host <claude-code|codex|gemini|cursor|opencode|hermes> --project /path/to/gateway-data
```

The installer puts the skills in `<project>/.agents/skills/`, links them where the host
looks (`--dir` overrides the location), and creates `.agents/skills/ignition-local/` for
project-specific rules. It prints any final step the host needs, such as appending a
snippet to `AGENTS.md` or running `hermes skills trust`.

## Guard rails (optional)

Add `--hook` to the install command on Claude Code or Hermes to install a hook that blocks
direct writes to `config/resources/**` and `projects/**`, so `ign` stays the only writer of
gateway files. The installer prints the one settings file to merge afterwards
(`hosts/claude-code/settings.example.json` or `hosts/hermes/config.example.yaml`).

## Skills

| Skill | Covers |
|---|---|
| `ignition-setup` | Install `ign`, configure `.env`, verify the gateway, the rules every other skill assumes |
| `ignition-tag` | Tags, UDT types and instances, alarms |
| `ignition-view` | Perspective views, bindings, transforms, pages, session props, scripts, style classes, themes, runtime validation |
| `ignition-provider` | Tag provider CRUD and the resources/projects API rules |
| `ignition-db` | Database connections, alarm journals, JDBC drivers, password handling |
| `ignition-api` | Raw `/data/api/v1/*` calls, the OpenAPI spec, gateway logs |
| `ignition-component` | The `ia.*` component inventory and valid icon glyphs |
| `ignition-manifest` | Push manifests and `ign diff` for idempotent writes |
| `ignition-disk` | Read-only inspection of `config/resources/` and `projects/`, scans |
| `skill-learn` | Fold the user's hand-edits of generated work into the project's local skill |

Each skill is a short `SKILL.md` plus `references/*.md` loaded only when needed.

## Project-specific knowledge

The skills never modify themselves. Anything the agent learns about a particular gateway
goes in `<project>/.agents/skills/ignition-local/`. Generic lessons are welcome as pull
requests against `skills/*/references/`; `docs/design/lessons.md` holds the reasoning
behind the skills.

## Layout

```
skills/<name>/SKILL.md            the skill
skills/<name>/references/*.md     lazy-loaded detail
hosts/<host>/                     per-host adapters (hook, settings, snippets)
install.sh                        per-host installer
docs/design/lessons.md            strategies and best practices behind the skills
.claude-plugin/                   Claude Code plugin + marketplace manifests
```

## License

Apache-2.0.
