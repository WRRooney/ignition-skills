# Skill authoring gotchas

Checks to run before appending to any `SKILL.md`, whether by hand or through the reflect step.

## Inline shell-exec glyphs are evaluated by some loaders

Rules:

- Never put the literal sequence (exclamation mark, backtick, text, backtick) in skill prose, not even to warn about it. Describe it in words, as this file does.
- Fenced code blocks are not reliably exempt. Keep shell examples free of a leading exclamation mark before a backtick.
- Audit before committing a skill change. The pattern below finds an exclamation mark followed by a backtick-delimited span:

  ```bash
  grep -rnE '![`][^`]+[`]' .agents/skills/ */SKILL.md
  ```

  Any hit in prose is a latent load failure.

## Frontmatter

- Only `name:` and `description:` in the frontmatter for portable skills. Host-specific keys (`allowed-tools`, `argument-hint`) belong in a host adapter, not in a shared skill.
- The description says when to use the skill and when not to, with trigger phrases and explicit non-triggers. Keep it under about 800 characters.

## Content hygiene for appended blocks

- No dates of discovery, session ids, ticket numbers, or "verified on" notes.
- No secrets, hostnames, ports, or tokens from the user's environment in a shared skill. In the project-local skill a host URL is acceptable; a token never is.
- Commands must match the tool's current `--help`. Re-check before appending a command example.
- `SKILL.md` is a router: rules that apply to every task, then a table sending each task or problem to one reference file. Commands and examples live in `references/`, one task or topic per file. A new reference gets a row in that table.
- Write what the agent should do. No backstory of how a rule was found and no background the agent does not need for the task.
