#!/usr/bin/env python3
"""Run network-isolated tests and save a machine-readable, bounded receipt."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1] / "src"
proof = ROOT.parent / ".test-results"
proof.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONPATH=str(ROOT / "box/tests/support"))
env["BOX_WORKFLOW_SOURCE"] = str(ROOT / "box/workflows.py")
suites = [
    ("independent-evidence", ["../tests/audit/test_evidence_independent.py"]),
    ("gather-evidence", ["-m", "unittest", "discover", "-s", "box/tests", "-p", "test_gather_evidence.py", "-v"]),
    ("redirect-diagnostics", ["-m", "unittest", "discover", "-s", "box/tests", "-p", "test_redirect_diagnostics.py", "-v"]),
    ("release-edges", ["../tests/audit/test_release_edges.py", "box"]),
    ("resource-limits", ["../tests/audit/test_resource_edges.py", "box"]),
    ("bounded-transport", ["../tests/audit/test_bounded_transport.py", "box"]),
    ("independent-workflow-audit", ["../tests/audit/test_independent_workflows.py"]),
    ("packaging", ["../tests/test_packaging.py"]),
    ("independent-core", ["box/tests/independent_archive.py", "box/bin/box"]),
    ("independent-enterprise", ["box/tests/independent_enterprise.py", "box/workflows.py"]),
    ("enterprise", ["box/tests/test_workflows.py"]),
    ("workflow-contract", ["-m", "unittest", "discover", "-s", "box/tests", "-p", "test_workflow_contract.py", "-v"]),
    ("unit", ["box/tests/test_retry.py"]),
    ("regression", ["box/tests/test_regression.py"]),
    ("contract", ["-m", "unittest", "discover", "-s", "box/tests", "-p", "test_api_contract.py", "-v"]),
    ("cli-workflow", ["-m", "unittest", "discover", "-s", "box/tests", "-p", "test_cli_workflow.py", "-v"]),
]
results = []
for name, args in suites:
    proc = subprocess.run([sys.executable, *args], cwd=ROOT, env=env, capture_output=True, text=True, timeout=45)
    log = proof / (name + ".txt")
    log.write_text(proc.stdout + proc.stderr)
    results.append({"suite": name, "exit_code": proc.returncode, "log": str(log.relative_to(ROOT.parent))})
    print(name + ": " + ("PASS" if proc.returncode == 0 else "FAIL"))
files = sorted(p for p in (ROOT / "box").rglob("*") if p.is_file() and "__pycache__" not in p.parts)
receipt = {"kind": "offline synthetic transport", "live_box_verified": False,
           "muse_verified": False, "refresh_verified": False, "suites": results,
           "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(proof / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
raise SystemExit(any(r["exit_code"] != 0 for r in results))
