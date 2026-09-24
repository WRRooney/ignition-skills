#!/usr/bin/env python3
"""Pre-tool-call guard: block tool calls that WRITE Ignition gateway files.

Files under ``config/resources/**`` and ``projects/**`` of a gateway data dir
are written only by the ``ign`` CLI (ignition-gen-sdk), which validates them
through Pydantic models. One script serves two hosts:

  * Claude Code ``PreToolUse(Bash)``: settings ``deny`` rules stop Write/Edit;
    this closes the shell vector (redirects, tee, cp/mv/rm/sed -i, in-line
    Python writes).
  * Hermes ``pre_tool_call`` (matcher ``terminal|execute_code|write_file|patch``):
    Hermes has no deny rules, so ``write_file``/``patch`` paths are checked here
    too, including V4A ``*** Update File:`` headers.

Protected targets:
  * relative ``config/resources/`` and ``projects/``, when cwd is the gateway data
    dir (the usual case: ``ign`` treats an unset ``IGNITION_DATA_DIR`` as cwd) or a
    workspace set up for it (``.agents/skills/ignition-setup/`` or ``IGNITION_*`` in ``.env``)
  * the same two trees under ``$IGNITION_DATA_DIR`` (env, or ``.env`` in cwd)
Absolute paths elsewhere that merely contain ``projects/`` are not protected.

Contract, by host (detected from the payload shape):
  * Claude Code sends ``tool_input``: block = exit 2 with the reason on stderr;
    allow = exit 0.
  * Hermes sends ``args``: block = exit 0 with ``{"action": "block", "message"}``
    on stdout; allow = exit 0 with ``{}`` (fail_closed treats other stdout as a
    failure). Hermes hooks are global, not per-project, so relative paths are
    protected only when the hook's working directory is the gateway data dir
    (see above); ``IGNITION_DATA_DIR`` trees are protected from anywhere.
Fails open on malformed input so it never wedges the agent, and says so on stderr.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REL = r"(?<![\w/~.])(?:\./)?(?:config/resources|projects)/"


def _data_dir() -> str | None:
    val = os.environ.get("IGNITION_DATA_DIR")
    if not val:
        try:
            for line in Path(".env").read_text(encoding="utf-8").splitlines():
                if line.startswith("IGNITION_DATA_DIR="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
        except OSError:
            return None
    return val or None


def _cwd_is_ignition() -> bool:
    if Path("config/resources").is_dir() or Path(".agents/skills/ignition-setup").is_dir():
        return True
    try:
        return "IGNITION_" in Path(".env").read_text(encoding="utf-8")
    except OSError:
        return False


def _protected_pattern() -> str:
    parts = [REL] if _cwd_is_ignition() else []
    dd = _data_dir()
    if dd:
        root = re.escape(dd.rstrip("/"))
        parts.append(root + r"/(?:config/resources|projects)/")
    return "(?:" + "|".join(parts) + ")" if parts else r"(?!)"


def violation_patterns() -> list[re.Pattern[str]]:
    p = _protected_pattern()
    return [
        re.compile(r">>?\s*['\"]?" + p),                                   # > / >> redirect
        re.compile(r"\btee\b(?:\s+-\S+)*\s+['\"]?" + p),                   # tee
        re.compile(r"\b(?:sed\s+-i\S*|cp|mv|rm|dd|truncate|install|ln|rsync)\b[^|;&]*?['\"]?" + p),
    ]


PY_WRITE = re.compile(
    r"(?:json\.dump\(|\.write_text\(|\.write_bytes\(|\.write\(|open\([^)]*['\"][wax]|shutil\.(?:copy|move|rmtree))"
)


def is_violation(cmd: str) -> bool:
    for rx in violation_patterns():
        if rx.search(cmd):
            return True
    literal = re.compile(r"['\"]" + _protected_pattern())
    return bool(PY_WRITE.search(cmd) and literal.search(cmd))


V4A_FILE = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", re.M)


def is_protected_path(path: str) -> bool:
    p = os.path.normpath(os.path.join(os.getcwd(), os.path.expanduser(path)))
    roots = [os.getcwd()] if _cwd_is_ignition() else []
    dd = _data_dir()
    if dd:
        roots.append(os.path.normpath(os.path.expanduser(dd)))
    return any(p.startswith(os.path.join(r, t) + os.sep) for r in roots for t in ("config/resources", "projects"))


def check(tool: str, args: dict) -> bool:
    """True when the call writes a protected file."""
    if tool in ("write_file", "patch"):
        paths = [args.get("path") or ""] + V4A_FILE.findall(args.get("patch") or "")
        return any(is_protected_path(x.strip()) for x in paths if x.strip())
    cmd = args.get("command") or args.get("code") or ""  # Bash/terminal, or Hermes execute_code
    if not cmd:
        return False
    if re.match(r"\s*(?:cd\s+[^&;|]+&&\s*)?git\s", cmd):  # version control is not authoring
        return False
    return is_violation(cmd)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception as e:  # noqa: BLE001
        print(f"[block_ignition_disk_writes] parse error, allowing: {e}", file=sys.stderr)
        return 0
    if data.get("cwd"):  # not a documented field on either host; honored when present
        try:
            os.chdir(data["cwd"])
        except OSError:
            pass
    hermes = "args" in data and "tool_input" not in data
    args = data.get("args") if hermes else data.get("tool_input")
    if not check(data.get("tool_name") or "", args or {}):
        print("{}")  # explicit no-op: Hermes fail_closed treats unparseable stdout as a block
        return 0
    reason = (
        "BLOCKED: direct write to an Ignition file (config/resources/** or projects/**). "
        "Only the `ign` CLI writes these files. If no `ign` verb expresses the shape you need, "
        "extend the ignition-gen-sdk model and CLI, then run `ign`; never hand-write gateway JSON."
    )
    if hermes:
        print(json.dumps({"action": "block", "message": reason}))
        return 0
    print(reason, file=sys.stderr)
    return 2

if __name__ == "__main__":
    sys.exit(main())
