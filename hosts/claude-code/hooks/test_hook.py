"""Run: python3 hosts/claude-code/hooks/test_hook.py  (exit 0 = every case behaves)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
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


def run(cmd: str) -> int:
    env = {**os.environ, "IGNITION_DATA_DIR": DD}
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}),
        capture_output=True,
        text=True,
        env=env,
    )
    return r.returncode


results = [(c, run(c), want) for c, want in CASES.items()]
bad = [(c, got, want) for c, got, want in results if got != want]
for c, got, want in bad:
    print(f"BAD exit={got} want={want}: {c}")
print(f"{len(CASES) - len(bad)}/{len(CASES)} ok")
sys.exit(1 if bad else 0)
