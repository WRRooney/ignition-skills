# File schemas

Both files live in `.agents/skill-feedback/<topic>/`. Frontmatter is plain YAML; the `status` field drives `skill-learn list`.

## BASELINE.md

```markdown
---
topic: pump-views
created: <ISO date>
baseline_sha: <full SHA>
status: snapshot            # snapshot | pending-review | applied
---

## What the agent wrote

One paragraph: what was produced, which commands or generators produced it, which commit.

## Scope (paths to diff later)

- projects/Demo/com.inductiveautomation.perspective/views/Equipment/Pump/**
- .ign_tools/build_pump_views.py

## Skill targets

- .agents/skills/ignition-local/SKILL.md
- .agents/skills/ignition-local/references/perspective-conventions.md

## Open questions

1. Whether the status badge should be a style class swap or an expression-bound color.
2. Whether the header binds the instance's meta_label or the tag name.
```

## LEARNINGS.md

```markdown
---
topic: pump-views
reflected: <ISO date>
baseline_sha: <SHA>
head_sha: <SHA>
status: pending-review      # pending-review | applied
---

## Diff summary

- 6 files changed inside scope
- 84 insertions, 31 deletions

## Pattern table

| Path | Change | Lesson | Target | Confidence |
|------|--------|--------|--------|------------|
| views/Equipment/Pump/view.json root.props.style.classes | expression binding replaced by a style.classes swap | Use one style class per state and bind style.classes; do not bind color directly | ignition-local/SKILL.md | high |

## Proposed additions

### .agents/skills/ignition-local/SKILL.md

~~~markdown
## Equipment state styling

Use one style class per equipment state and bind `style.classes`. Do not bind `style.color` or `backgroundColor` directly; the theme owns colors.
~~~

### .agents/skills/ignition-local/references/perspective-conventions.md

~~~markdown
...
~~~
```

Blocks are appended verbatim after approval. Keep each block self-contained: a heading and a few sentences or a short table. When a proposed block would duplicate an existing section in the target, propose an edit to that section instead and mark it as such.

## Tag naming

`skill-feedback/<topic>/baseline`, lightweight, moved with `git tag -f`. One tag per topic; a second snapshot of the same topic moves it, and the previous `BASELINE.md` is overwritten only after its status is `applied`.
