# Project layout

Three directories sit next to `.env` in the user's project. Only `.ign/` is regenerable.

## `.ign/` (SDK state, gitignored)

Written by the first-use spec fetch and client generation, `ign openapi docs`, `ign view validate`, and the manifest recorder behind push verbs. Safe to delete; the next typed verb refetches and regenerates, and `ign openapi docs` re-renders the reference.

## `.ign_tools/` (the user's generators, committed)

One Python file per tool; the file stem is the tool name and the module docstring's first line is its description.

```bash
ign tools list                   # name + description for every .ign_tools/*.py
ign tools run build_pumps --dry-run
```

`ign tools run NAME [ARGS]...` executes `.ign_tools/NAME.py` as `__main__` with the remaining arguments. Tools import `ignition_gen_sdk` like any script and write through the same backends the CLI uses. Rules for a tool:

- It is a seed for a whole family of resources, not a patch tool. Never re-run a generator over views a person has edited in the Designer; the guard in `ignition_gen_sdk.tools.seed_guard` refuses to overwrite an existing `view.json` unless `--force` is passed.
- It is committed and reviewable. A tool that no longer matches anything live belongs in git history, not in `.ign_tools/`.
- Missing CLI capability is still an SDK bug. A tool is for repetition, not for reaching internals the CLI does not expose.

## `.agents/skills/ignition-local/` (project learnings, committed)

The installed plugin skills are generic and never self-modify. Gateway-specific facts go here, and the agent appends to this file as it learns. Starter template:

```markdown
---
name: ignition-local
description: Project-specific Ignition facts for this repository. Read before any ign work here.
---

## Gateway

- URL: (host-reachable base URL; no token)
- Backend: disk (data dir at ...) | API-only
- Gateway version: (from `ign openapi fetch` output or `ign api GET /data/api/v1/gateway-info`)

## Providers

| Provider | Notes |
|---|---|
| default | (permission quirks, purpose) |

## Projects

| Project | Parent | Notes |
|---|---|---|
| Demo | | |

## Conventions

- Tag path style, naming rules, folder layout.

## Gotchas

- (date-free, one line each, with the verb or endpoint involved)
```

When a gotcha is general to Ignition 8.3 rather than to this gateway, it belongs upstream in the public skills repository; note it here first, then open an issue or pull request there.
