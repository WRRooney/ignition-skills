#!/usr/bin/env python3
"""Lint the skills tree. Exit 1 on any finding.

Checks every ``skills/<name>/SKILL.md``:
  * frontmatter has exactly ``name`` (matching the directory) and ``description`` (80..1024 chars)
  * every ``references/*.md`` file is linked from SKILL.md, and every linked reference exists
  * skills/ and docs/ stay host-neutral (no ``Claude``), since they install into any agent host
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def frontmatter(text: str) -> dict[str, str] | None:
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        return None
    out: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^[A-Za-z_-]+:", line):
            key, _, val = line.partition(":")
            out[key.strip()] = val.strip().lstrip("|").strip()
        elif key and line.startswith(" "):
            out[key] += " " + line.strip()
    return out


def main() -> int:
    problems: list[str] = []
    for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
        name = skill_md.parent.name
        text = skill_md.read_text(encoding="utf-8")
        fm = frontmatter(text)
        if fm is None:
            problems.append(f"{name}: missing frontmatter")
            continue
        if set(fm) != {"name", "description"}:
            problems.append(f"{name}: frontmatter keys {sorted(fm)}; want exactly name + description")
        if fm.get("name") != name:
            problems.append(f"{name}: frontmatter name {fm.get('name')!r} != directory")
        if len(fm.get("description", "")) > 1024 or len(fm.get("description", "")) < 80:
            problems.append(f"{name}: description length {len(fm.get('description', ''))} (want 80..1024)")
        refs_dir = skill_md.parent / "references"
        on_disk = {p.name for p in refs_dir.glob("*.md")} if refs_dir.is_dir() else set()
        linked = set(re.findall(r"references/([A-Za-z0-9._-]+\.md)", text))
        for missing in sorted(on_disk - linked):
            problems.append(f"{name}: references/{missing} exists but SKILL.md never links it")
        for dangling in sorted(linked - on_disk):
            problems.append(f"{name}: SKILL.md links references/{dangling} which does not exist")
    for path in sorted(list((ROOT / "skills").rglob("*.md")) + list((ROOT / "docs").rglob("*.md"))):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"\bClaude\b(?! Code)", text):  # the host name is fine; "Claude does X" is not
            line = text.count("\n", 0, m.start()) + 1
            problems.append(f"{rel}:{line}: host-specific term 'Claude'; keep skills host-neutral")
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
