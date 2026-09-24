#!/usr/bin/env sh
# Install ignition-skills into a project for one agent host.
#
#   install.sh --host claude-code|codex|gemini|cursor|opencode|hermes [--project DIR] [--hook] [--dir SKILLS_DIR]
#
# Skills are copied ONCE into <project>/.agents/skills/ (the neutral, tool-independent
# location) and then symlinked into the host's own skills directory. --dir overrides
# that host directory when your host reads skills from somewhere else. Hermes reads
# .agents/skills/ directly, so it gets no symlinks.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
HOST=""; PROJECT="$PWD"; HOOK=0; HOSTDIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --host) HOST=$2; shift 2 ;;
    --project) PROJECT=$2; shift 2 ;;
    --hook) HOOK=1; shift ;;
    --dir) HOSTDIR=$2; shift 2 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$HOST" ] || { echo "--host is required" >&2; exit 2; }

case "$HOST" in
  claude-code) DEFAULT_DIR=".claude/skills" ;;
  codex)       DEFAULT_DIR=".codex/skills" ;;
  gemini)      DEFAULT_DIR=".gemini/skills" ;;
  cursor)      DEFAULT_DIR=".cursor/skills" ;;
  opencode)    DEFAULT_DIR=".opencode/skills" ;;
  hermes)      DEFAULT_DIR=".agents/skills" ;;
  *) echo "unknown host: $HOST" >&2; exit 2 ;;
esac
HOSTDIR=${HOSTDIR:-$DEFAULT_DIR}

NEUTRAL="$PROJECT/.agents/skills"
mkdir -p "$NEUTRAL" "$PROJECT/$HOSTDIR"
link() {  # link NAME: symlink $NEUTRAL/NAME into the host dir; never clobber a real directory
  [ "$PROJECT/$HOSTDIR" -ef "$NEUTRAL" ] && return 0  # host reads the neutral dir itself
  target="$PROJECT/$HOSTDIR/$1"
  if [ -d "$target" ] && [ ! -L "$target" ]; then
    echo "skip: $target is a real directory (your own skill?); remove it to install the shared one" >&2
    return 0
  fi
  ln -sfn "$(realpath --relative-to="$PROJECT/$HOSTDIR" "$NEUTRAL/$1")" "$target"
}

for s in "$HERE"/skills/*/; do
  name=$(basename "$s")
  rm -rf "$NEUTRAL/$name"
  cp -R "$s" "$NEUTRAL/$name"
  link "$name"
done
mkdir -p "$NEUTRAL/ignition-local/references"
[ -f "$NEUTRAL/ignition-local/SKILL.md" ] || cat > "$NEUTRAL/ignition-local/SKILL.md" <<'SKILL'
---
name: ignition-local
description: Project-specific Ignition conventions and gotchas learned while working on THIS gateway. Read after the ignition-* skills. Append here; never edit the installed ignition-* skills.
---

# Local Ignition conventions

(Empty. The agent appends rules and gotchas discovered on this gateway. One heading per topic; details in references/.)
SKILL
link ignition-local

echo "skills: $NEUTRAL -> $PROJECT/$HOSTDIR"

case "$HOST" in
  claude-code)
    if [ "$HOOK" = 1 ]; then
      mkdir -p "$PROJECT/.claude/hooks"
      cp "$HERE/hosts/claude-code/hooks/block_ignition_disk_writes.py" "$PROJECT/.claude/hooks/"
      echo "hook: $PROJECT/.claude/hooks/block_ignition_disk_writes.py"
      echo "Now merge hosts/claude-code/settings.example.json into $PROJECT/.claude/settings.json."
    fi ;;
  codex|opencode) echo "Append hosts/$HOST/AGENTS.snippet.md to $PROJECT/AGENTS.md" ;;
  hermes)
    echo "Append hosts/hermes/AGENTS.snippet.md to $PROJECT/AGENTS.md (or .hermes.md if the project has one: Hermes loads only the first it finds)"
    echo "Then run \`hermes skills trust\` inside $PROJECT once; project skills stay unloaded until trusted."
    if [ "$HOOK" = 1 ]; then
      HOOKDIR="${HERMES_HOME:-$HOME/.hermes}/agent-hooks"
      mkdir -p "$HOOKDIR"
      cp "$HERE/hosts/claude-code/hooks/block_ignition_disk_writes.py" "$HOOKDIR/"
      chmod +x "$HOOKDIR/block_ignition_disk_writes.py"
      echo "hook: $HOOKDIR/block_ignition_disk_writes.py"
      echo "Now merge hosts/hermes/config.example.yaml into ${HERMES_HOME:-$HOME/.hermes}/config.yaml."
    fi ;;
  gemini)         echo "Append hosts/gemini/GEMINI.snippet.md to $PROJECT/GEMINI.md" ;;
  cursor)         mkdir -p "$PROJECT/.cursor/rules" && cp "$HERE/hosts/cursor/ignition.mdc" "$PROJECT/.cursor/rules/" && echo "rule: $PROJECT/.cursor/rules/ignition.mdc" ;;
esac
