#!/usr/bin/env python3
"""PreToolUse(Bash) guard: block Bash commands that WRITE Ignition gateway files.

Files under ``config/resources/**`` and ``projects/**`` of a gateway data dir
are written only by the ``ign`` CLI (ignition-gen-sdk), which validates them
through Pydantic models. Settings ``deny`` rules stop the Write/Edit tools;
this hook closes the Bash vector (redirects, tee, cp/mv/rm/sed -i, in-line
Python writes).

Protected targets:
  * relative ``config/resources/`` and ``projects/`` (the agent's cwd is the data dir)
  * the same two trees under ``$IGNITION_DATA_DIR`` (env, or ``.env`` in cwd)
Absolute paths elsewhere that merely contain ``projects/`` are not protected.

Contract: read the PreToolUse JSON on stdin; exit 2 with a reason on stderr to
block; exit 0 otherwise. Fails open on malformed input so it never wedges the
agent, and says so on stderr.
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


def _protected_pattern() -> str:
    parts = [REL]
    dd = _data_dir()
    if dd:
        root = re.escape(dd.rstrip("/"))
        parts.append(root + r"/(?:config/resources|projects)/")
    return "(?:" + "|".join(parts) + ")"


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


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception as e:  # noqa: BLE001
        print(f"[block_ignition_disk_writes] parse error, allowing: {e}", file=sys.stderr)
        return 0
    cmd = (data.get("tool_input", {}) or {}).get("command", "") or ""
    if not cmd:
        return 0
    if re.match(r"\s*(?:cd\s+[^&;|]+&&\s*)?git\s", cmd):  # version control is not authoring
        return 0
    if not is_violation(cmd):
        return 0
    print(
        "BLOCKED: direct Bash write to an Ignition file (config/resources/** or projects/**). "
        "Only the `ign` CLI writes these files. If no `ign` verb expresses the shape you need, "
        "extend the ignition-gen-sdk model and CLI, then run `ign`; never hand-write gateway JSON.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
