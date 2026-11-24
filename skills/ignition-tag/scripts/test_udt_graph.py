#!/usr/bin/env python3
"""Self-check for udt_graph.py: python3 test_udt_graph.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT = {"name": "", "tagType": "Provider", "tags": [
    {"name": "_types_", "tagType": "Folder", "tags": [
        {"name": "Lib", "tagType": "Folder", "tags": [
            {"name": "Vec", "tagType": "UdtType", "tags": []},
            {"name": "Base", "tagType": "UdtType", "tags": [
                {"name": "pos", "tagType": "UdtInstance", "typeId": "Lib/Vec"}]},
            {"name": "Child", "tagType": "UdtType", "typeId": "Lib/Base", "tags": [
                {"name": "Status", "tagType": "Folder", "tags": [{"name": "Fault", "tagType": "AtomicTag"}]},
                {"name": "Speed_duplicate_1", "tagType": "AtomicTag"}]},
            {"name": "Other", "tagType": "UdtType", "tags": []},
        ]}]},
    {"name": "Area", "tagType": "Folder", "tags": [
        {"name": "C1", "tagType": "UdtInstance", "typeId": "Lib/Child", "tags": [
            {"name": "Status", "tagType": "Folder", "tags": [{"name": "Fault", "tagType": "AtomicTag", "value": 1}]}]},
        {"name": "O1", "tagType": "UdtInstance", "typeId": "Lib/Other"}]},
]}


def run(*args):
    r = subprocess.run([sys.executable, os.path.join(HERE, "udt_graph.py"), *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


with tempfile.TemporaryDirectory() as d:
    exp = os.path.join(d, "e.json")
    json.dump(EXPORT, open(exp, "w"))

    rc, out = run(exp, "impact", "Lib/Vec")
    assert rc == 0, out
    order = [line.split()[0] for line in out.splitlines() if line.startswith("  Lib/")]
    assert order == ["Lib/Vec", "Lib/Base", "Lib/Child"], order
    assert "Affected instances: 1" in out and "Area/C1" in out and "Area/O1" not in out, out

    rc, out = run(exp, "order", "Lib/Child", "Lib/Vec", "Lib/Base")
    assert [line.strip() for line in out.splitlines()[1:]] == ["Lib/Vec", "Lib/Base", "Lib/Child"], out

    new = os.path.join(d, "n.json")
    json.dump({"name": "Orphan", "tagType": "UdtType", "typeId": "Lib/Nope"}, open(new, "w"))
    rc, out = run(exp, "order", "--new", f"Lib:{new}")
    assert rc == 1 and "missing dependency: Lib/Orphan needs Lib/Nope" in out, out

    rc, out = run(exp, "collide", "Lib/Base", "status/fault", "Other")
    assert rc == 1, out
    assert "type Lib/Child: declares Status/Fault" in out and "instance Area/C1 (Lib/Child): overrides Status/Fault" in out, out
    assert "2 collision(s)" in out, out
    rc, out = run(exp, "collide", "Lib/Base", "NewMember")
    assert rc == 0 and "0 collision(s)" in out, out

    rc, out = run(exp, "duplicates")
    assert rc == 1 and "type member Lib/Child/Speed_duplicate_1" in out and "1 duplicate(s)" in out, out

print("udt_graph ok")
