#!/usr/bin/env python3
"""Turn the Ignition write guard on or off for an agent host.

    python3 guardrails.py on|off|status [--host claude-code|hermes|all] [--project DIR]

The guard is one script, block_ignition_disk_writes.py (next to this file), that
blocks direct writes to config/resources/** and projects/** so the ign CLI stays the
only writer of gateway files.

claude-code: copies the hook to <project>/.claude/hooks/ and edits
    <project>/.claude/settings.json (PreToolUse hook on Bash + deny rules for Write/Edit).
hermes:      copies the hook to $HERMES_HOME/agent-hooks/ (default ~/.hermes/agent-hooks/)
    and edits $HERMES_HOME/config.yaml (hooks.pre_tool_call entry, fail_closed).
all (default): every host detected (<project>/.claude/ exists, $HERMES_HOME exists).

Both edits are idempotent and reversible; off removes exactly what on added.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK_SRC = HERE / "block_ignition_disk_writes.py"
HOOK_NAME = HOOK_SRC.name
DENY = ["Write(config/resources/**)", "Edit(config/resources/**)", "Write(projects/**)", "Edit(projects/**)"]
ALLOW = ["Bash(ign *)"]
HERMES_MATCHER = "terminal|execute_code|write_file|patch"


def _hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")


# ---------------------------------------------------------------- claude-code

def _cc_paths(project: Path) -> tuple[Path, Path]:
    return project / ".claude" / "hooks" / HOOK_NAME, project / ".claude" / "settings.json"


def _cc_hook_entry() -> dict:
    return {"matcher": "Bash", "hooks": [{"type": "command", "command": f"python3 .claude/hooks/{HOOK_NAME}"}]}


def _is_our_cc_entry(entry: dict) -> bool:
    return any(HOOK_NAME in (h.get("command") or "") for h in entry.get("hooks", []))


def cc_on(project: Path) -> None:
    hook, settings = _cc_paths(project)
    hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HOOK_SRC, hook)
    cfg = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    perms = cfg.setdefault("permissions", {})
    for key, rules in (("deny", DENY), ("allow", ALLOW)):
        lst = perms.setdefault(key, [])
        lst.extend(r for r in rules if r not in lst)
    pre = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if not any(_is_our_cc_entry(e) for e in pre):
        pre.append(_cc_hook_entry())
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"claude-code: on  ({hook}, {settings})")


def cc_off(project: Path) -> None:
    hook, settings = _cc_paths(project)
    if hook.exists():
        hook.unlink()
    if settings.exists():
        cfg = json.loads(settings.read_text(encoding="utf-8"))
        perms = cfg.get("permissions", {})
        for key, rules in (("deny", DENY), ("allow", ALLOW)):
            if key in perms:
                perms[key] = [r for r in perms[key] if r not in rules]
                if not perms[key]:
                    del perms[key]
        if not perms:
            cfg.pop("permissions", None)
        pre = cfg.get("hooks", {}).get("PreToolUse")
        if pre is not None:
            cfg["hooks"]["PreToolUse"] = [e for e in pre if not _is_our_cc_entry(e)]
            if not cfg["hooks"]["PreToolUse"]:
                del cfg["hooks"]["PreToolUse"]
            if not cfg["hooks"]:
                del cfg["hooks"]
        settings.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"claude-code: off ({project})")


def cc_status(project: Path) -> str:
    hook, settings = _cc_paths(project)
    wired = False
    if settings.exists():
        cfg = json.loads(settings.read_text(encoding="utf-8"))
        wired = any(_is_our_cc_entry(e) for e in cfg.get("hooks", {}).get("PreToolUse", []))
    return "on" if hook.exists() and wired else "off"


# --------------------------------------------------------------------- hermes

def _hermes_paths() -> tuple[Path, Path]:
    home = _hermes_home()
    return home / "agent-hooks" / HOOK_NAME, home / "config.yaml"


def _yaml():
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        print("hermes: PyYAML is not importable; edit config.yaml by hand with hosts/hermes/config.example.yaml", file=sys.stderr)
        return None
    return yaml


def _is_our_hermes_entry(entry: dict) -> bool:
    return HOOK_NAME in str(entry.get("command") or "")


def hermes_on() -> None:
    hook, config = _hermes_paths()
    hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HOOK_SRC, hook)
    hook.chmod(0o755)
    yaml = _yaml()
    if yaml is None:
        return
    cfg = (yaml.safe_load(config.read_text(encoding="utf-8")) if config.exists() else None) or {}
    pre = cfg.setdefault("hooks", {}).setdefault("pre_tool_call", [])
    if not any(_is_our_hermes_entry(e) for e in pre):
        pre.append({"matcher": HERMES_MATCHER, "command": str(hook), "timeout": 10, "fail_closed": True})
    config.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    print(f"hermes: on  ({hook}, {config}); Hermes asks for consent on first use")


def hermes_off() -> None:
    hook, config = _hermes_paths()
    if hook.exists():
        hook.unlink()
    yaml = _yaml()
    if yaml is not None and config.exists():
        cfg = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        pre = cfg.get("hooks", {}).get("pre_tool_call")
        if pre is not None:
            cfg["hooks"]["pre_tool_call"] = [e for e in pre if not _is_our_hermes_entry(e)]
            if not cfg["hooks"]["pre_tool_call"]:
                del cfg["hooks"]["pre_tool_call"]
            if not cfg["hooks"]:
                del cfg["hooks"]
            config.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    print(f"hermes: off ({_hermes_home()})")


def hermes_status() -> str:
    hook, config = _hermes_paths()
    yaml = _yaml()
    wired = False
    if yaml is not None and config.exists():
        cfg = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        wired = any(_is_our_hermes_entry(e) for e in cfg.get("hooks", {}).get("pre_tool_call", []))
    return "on" if hook.exists() and wired else "off"


# ----------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["on", "off", "status"])
    ap.add_argument("--host", choices=["claude-code", "hermes", "all"], default="all")
    ap.add_argument("--project", default=".", help="gateway data dir (default: cwd)")
    a = ap.parse_args()
    project = Path(a.project).resolve()

    hosts = [a.host] if a.host != "all" else [
        h for h, present in (("claude-code", (project / ".claude").is_dir()), ("hermes", _hermes_home().is_dir())) if present
    ]
    if not hosts:
        print("no host detected: pass --host claude-code or --host hermes", file=sys.stderr)
        return 2
    for h in hosts:
        if a.action == "status":
            print(f"{h}: {cc_status(project) if h == 'claude-code' else hermes_status()}")
        elif h == "claude-code":
            (cc_on if a.action == "on" else cc_off)(project)
        else:
            (hermes_on if a.action == "on" else hermes_off)()
    return 0


if __name__ == "__main__":
    sys.exit(main())
