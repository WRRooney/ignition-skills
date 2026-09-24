"""Run: python3 hosts/claude-code/hooks/test_hook.py  (exit 0 = every case behaves)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).with_name("block_ignition_disk_writes.py")
DD = "/srv/gateway/data"
P = "proj" + "ects"  # split so this file itself never trips a path guard
C = "config/res" + "ources"
CASES = {
    "uv tool install --editable /home/me/projects/ignition-gen-sdk": 0,
    "cp /home/me/projects/foo/x.json /tmp/y.json": 0,
    f"cat {P}/Demo/project.json": 0,
    f"git add {P}/Demo && git commit -m 'edit {P}/Demo'": 0,
    "ign view write --project Demo --view-path A/B": 0,
    f"cp x.json {P}/Demo/foo.json": 2,
    f"echo hi > ./{C}/core/x.json": 2,
    f"tee {P}/Demo/a.json < b": 2,
    f"sed -i 's/a/b/' {P}/Demo/view.json": 2,
    f"cp x.json {DD}/{P}/Demo/foo.json": 2,
    f"python3 -c \"open('{DD}/{C}/core/a.json','w').write('x')\"": 2,
    f"python3 -c \"import json; json.dump({{}}, open('{P}/Demo/a.json','w'))\"": 2,
    f"python3 -c \"print(open('{P}/Demo/a.json').read())\"": 0,
}
# Hermes pre_tool_call: (tool_name, tool_input, cwd is an Ignition dir?) -> exit code
PROJ = tempfile.mkdtemp()  # a gateway data dir: the usual cwd
(Path(PROJ) / C).mkdir(parents=True)
OTHER = tempfile.mkdtemp()
HERMES = [
    ("terminal", {"command": f"cp x.json {P}/Demo/foo.json"}, True, 2),
    ("terminal", {"command": f"cp x.json {P}/Demo/foo.json"}, False, 0),  # global hook, unrelated repo
    ("terminal", {"command": f"cp x.json {DD}/{P}/Demo/foo.json"}, False, 2),
    ("write_file", {"path": f"{P}/Demo/view.json", "content": "{}"}, True, 2),
    ("write_file", {"path": f"{PROJ}/{C}/core/a.json", "content": "{}"}, True, 2),
    ("write_file", {"path": f"{DD}/{P}/Demo/a.json", "content": "{}"}, False, 2),
    ("write_file", {"path": f"{P}/Demo/view.json", "content": "{}"}, False, 0),
    ("write_file", {"path": "notes.md", "content": "x"}, True, 0),
    ("patch", {"path": f"./{C}/core/x.json", "old_string": "a", "new_string": "b"}, True, 2),
    ("patch", {"mode": "patch", "patch": f"*** Begin Patch\n*** Update File: {P}/Demo/v.json\n*** End Patch"}, True, 2),
    ("patch", {"mode": "patch", "patch": "*** Begin Patch\n*** Update File: README.md\n*** End Patch"}, True, 0),
    ("execute_code", {"code": f"open('{P}/Demo/a.json','w').write('x')"}, True, 2),
    ("read_file", {"path": f"{P}/Demo/a.json"}, True, 0),
]
WS = tempfile.mkdtemp()  # a workspace set up by install.sh, data dir elsewhere
(Path(WS) / ".agents/skills/ignition-setup").mkdir(parents=True)
ENV = tempfile.mkdtemp()  # a workspace set up by ignition-setup's .env only
(Path(ENV) / ".env").write_text("IGNITION_URL=http://gw:8088\n")
MARKERS = [(WS, 2), (ENV, 2), (OTHER, 0)]


def run(tool: str, args: dict, cwd: str, hermes: bool = False) -> tuple[int, str]:
    """Claude Code shape (tool_input; exit 2 blocks) or Hermes shape (args; stdout directive blocks).

    Returns (verdict, stdout); verdict is 2 for a block on either host."""
    env = {**os.environ, "IGNITION_DATA_DIR": DD}
    payload = {"tool_name": tool, ("args" if hermes else "tool_input"): args}
    r = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=cwd,
    )
    if not hermes:
        return r.returncode, r.stdout
    if r.returncode != 0:
        return -1, r.stdout  # Hermes hooks must exit 0 either way
    try:
        return (2 if json.loads(r.stdout).get("action") == "block" else 0), r.stdout
    except ValueError:
        return -1, r.stdout  # unparseable stdout would make fail_closed block everything


results = [(c, run("Bash", {"command": c}, PROJ), want) for c, want in CASES.items()]
results += [(f"hermes {t} {a}", run(t, a, PROJ if proj else OTHER, hermes=True), want) for t, a, proj, want in HERMES]
results += [(f"marker {d}", run("write_file", {"path": f"{P}/Demo/a.json"}, d, hermes=True), want) for d, want in MARKERS]
bad = [(c, got, want) for c, (got, out), want in results
       if got != want or (got == 0 and out.strip() != "{}")]  # allow prints {} so Hermes fail_closed passes  # allow must print {} for Hermes fail_closed
for c, got, want in bad:
    print(f"BAD exit={got} want={want}: {c}")
print(f"{len(results) - len(bad)}/{len(results)} ok")
sys.exit(1 if bad else 0)
