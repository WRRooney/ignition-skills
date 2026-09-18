---
name: skill-learn
description: |
  Use to turn a user's hand-edits of agent-generated work into durable skill guidance: snapshot with a git tag before the user edits, then diff afterward and propose per-block additions to the project's local skill (`.agents/skills/ignition-local/`). Offer it whenever the agent has just produced something the user will revise by hand (a view, a UDT family, a script). Also use when the user says they are done editing and wants the lessons captured.
  Positive triggers: "skill-learn", "snapshot before I edit", "I'm going to fix this by hand", "diff what I changed", "learn from my edits", "evolve the skill", "capture the lessons", "/skill-learn start", "/skill-learn diff".
  Do not trigger for: ordinary git diff or git tag requests, code review, PR review, or editing the installed plugin's own skills.
---

## Purpose

The agent writes a first pass. The user fixes what the agent got wrong. Without a capture step, those corrections evaporate at the end of the session and the next session repeats the mistake. This skill closes the loop in two steps:

1. **Snapshot** the state and the agent's intent before the user edits.
2. **Reflect** after the edits: diff, cluster, and propose additions to the relevant skill, one block at a time, for the user to accept or reject.

The user's edits are ground truth. The agent's job is to read them, not to defend the first pass.

## Where learned rules go

Learned rules are written to the user's project, never to the installed plugin:

```
.agents/skills/ignition-local/
  SKILL.md              project-specific facts and gotchas (the usual target)
  references/*.md       longer topic notes when a lesson outgrows a paragraph
.agents/skill-feedback/
  <topic>/
    BASELINE.md         scope, targets, open questions, baseline commit
    LEARNINGS.md        pattern table and proposed blocks (written by the reflect step)
```

If `.agents/skills/ignition-local/SKILL.md` does not exist, create it from the template in the `ignition-setup` skill first. A lesson that is true of Ignition 8.3 in general, not of this project, still lands in `ignition-local` first; note it as an upstream candidate so the user can send it to the public skills repository.

This skill uses plain git and plain files. It works the same under any agent host; hosts differ only in how the user invokes it (a slash command, a mention by name, or a request in prose).

## Step 1: Snapshot (`skill-learn start <topic>`)

Topic slug: kebab-case, at most 60 characters, `[a-z0-9-]` only.

1. Determine scope: the paths the user will edit (globs are fine). Confirm with the user in one line.
2. Refuse if the working tree is dirty inside the scope. The baseline must be a known state; ask the user to commit or stash the scope first. Dirt outside the scope is ignored.
3. Move or create the lightweight tag on HEAD:

   ```bash
   git tag -f skill-feedback/<topic>/baseline HEAD
   ```

4. Write `.agents/skill-feedback/<topic>/BASELINE.md` (schema in `references/file-schemas.md`): what the agent produced, the scope, the skill targets, and the agent's open questions. The open questions matter most; the user's edits in those areas are the highest-value signal.
5. Report: tag name, short SHA, scope, targets. Tell the user to come back with "diff it" when done.

Offer this step proactively. Right after producing anything of size that the user will refine by hand, say: "Want me to snapshot this for skill-learn before you edit?"

## Step 2: Reflect (`skill-learn diff <topic>`)

1. Read `BASELINE.md`; extract `baseline_sha`, scope, targets, open questions. Refuse if the tag is missing or its SHA disagrees with the file, and say why.
2. Collect both diffs over the scope:

   ```bash
   git diff <baseline_sha>...HEAD -- <scope>     # committed edits
   git diff -- <scope>                            # uncommitted edits
   git diff --stat <baseline_sha> -- <scope>      # for the summary line
   ```

3. Cluster by file, then by kind of change. For each cluster, one row:

   | Column | Content |
   |---|---|
   | Path | file, and section or property path if applicable |
   | Change | what moved, in one sentence |
   | Lesson | what the agent got wrong or what the user prefers, stated as a rule |
   | Target | one of the skill targets, or `none` for a one-off |
   | Confidence | `high` if it answers an open question, `medium` for a repeated pattern, `low` if it could be incidental |

4. Write `LEARNINGS.md` next to `BASELINE.md`: diff summary, the pattern table, and one proposed block per lesson. Each block is a literal, append-only addition to a named target file, phrased in that file's voice (present tense, concrete, with the verb or property involved).
5. Show the table and the blocks. Wait for explicit approval per block. Approved blocks are appended to the target; rejected blocks are removed from `LEARNINGS.md`; `low` rows are marked `defer` and kept for a future bundle.
6. Set `status: applied` in both frontmatters. Commit the skill changes and the feedback directory together if the user has asked the agent to commit.

## Step 3: List (`skill-learn list`)

Print every `.agents/skill-feedback/*/BASELINE.md` with its `topic` and `status` (`snapshot`, `pending-review`, `applied`). Tags can be listed with `git tag -l 'skill-feedback/*'`.

## Worked example

The agent generates a family of pump views into project `Demo` with `ign tools run build_pump_views`, then offers a snapshot:

```bash
git tag -f skill-feedback/pump-views/baseline HEAD
# BASELINE.md scope: projects/Demo/com.inductiveautomation.perspective/views/Equipment/Pump/**
# open question: style class swap vs. bound color for the state badge
```

The user spends an afternoon in the Designer. Later they say "diff it". The reflect step finds that every badge's `style.classes` is now bound to a state-named class and every direct color binding is gone, that the header label now reads the instance's `meta_label` instead of the tag name, and that the Designer re-sorted the `props` keys. The last item is Designer churn and is dropped. The first two become two `high` rows (they answer open questions) and two proposed blocks for `.agents/skills/ignition-local/SKILL.md`. The user accepts both, the agent appends them, sets `status: applied`, and commits.

## What counts as a lesson

- A shape the gateway wanted that the agent emitted differently (property name, nesting, enum literal).
- A convention the user applied consistently (naming, folder layout, spelling, which binding type to reach for).
- A default the user reversed every time (a verbose fallback removed, a script replaced by a binding).
- A verification step the user did that the agent skipped.

Not a lesson: a one-off value change, a typo fix, reformatting by the Designer on save (name-sorted arrays, integers for whole numbers). Recognize Designer churn and exclude it before clustering.

## Rules

- Never write to any `SKILL.md` or reference without per-block approval. The approval gate is the point of the skill.
- Never modify the installed plugin's skills. Targets are under the user's project only.
- Do not delete the baseline tag until `status: applied` is set; after that it is archival and may be pruned.
- Do not evolve a skill from a single `low` confidence signal.
- Phrase additions as rules with the verb, endpoint or property named, not as a story about what happened. Leave out dates and session references.
- Before appending to a skill file, run the checks in `references/skill-authoring-gotchas.md`.

## References

| File | Summary |
|---|---|
| `references/file-schemas.md` | Frontmatter and section layout for `BASELINE.md` and `LEARNINGS.md` |
| `references/skill-authoring-gotchas.md` | Text patterns that break skill loaders, and an audit command |
