# Skill authoring gotchas

Checks to run before appending to any `SKILL.md`, whether by hand or through the reflect step.

## Inline shell-exec glyphs are evaluated by some loaders

At least one agent host preprocesses `SKILL.md` for an inline shell-execution form: an exclamation mark immediately followed by a backtick-quoted command. The loader extracts the command and runs it through the shell before the skill text is shown to the model. It does this on every occurrence, including occurrences inside doubled backticks, inside prose, and inside a warning telling people not to use the form. Markdown escaping is a rendering convention; the loader's pattern match does not know about it.

Observed failure: loading a skill returned a "Shell command failed for pattern" error naming the glyph sequence, followed by a shell parse error near an angle bracket. A documentation sentence had contained the literal sequence with a placeholder in angle brackets, and the shell tried to treat the angle bracket as a redirection.

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

- No dates of discovery, session ids, ticket numbers, or "verified on" notes. The rule stands on its own or it is not a rule.
- No secrets, hostnames, ports, or tokens from the user's environment in a shared skill. In the project-local skill a host URL is acceptable; a token never is.
- American spelling. No em dashes; use commas, colons, or separate sentences.
- Commands must match the tool's current `--help`. Re-check before appending a command example.
- Keep `SKILL.md` between roughly 120 and 300 lines; move long material into `references/` files of 20 to 80 lines, one topic per file, and add a row to the References table.
