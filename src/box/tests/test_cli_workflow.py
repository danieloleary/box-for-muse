"""Process-level CLI workflows against a synthetic Box server boundary.

These tests do not establish Muse agent behavior, Box access, or token refresh.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / "state.json"
        files = []
        for number, (name, text) in enumerate([
            ("Approved proposal.txt", "Approved fee USD 24000. Delivery six weeks."),
            ("Draft proposal.txt", "UNAPPROVED draft fee USD 18000. Delivery four weeks."),
            ("Partner agreement.txt", "Term ends December 31, 2027. Non-renewal notice due October 2, 2027. Automatic renewal: one year."),
        ], start=1):
            files.append({"id": str(number), "parent": "9", "name": name, "version": str(number+10), "data": base64.b64encode(text.encode()).decode()})
        self.state.write_text(json.dumps({"files": files}))
        self.env = dict(os.environ, PYTHONPATH=str(ROOT / "tests" / "support"), BOX_TEST_STATE=str(self.state))

    def run_cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(ROOT / "bin" / "box"), *args], env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_search_read_save_and_new_process_readback(self):
        self.assertEqual(self.run_cli("identity")["id"], "100")
        first = self.run_cli("search", "proposal", "--folder-id", "9", "--limit", "1")
        self.assertFalse(first["complete"])
        second = self.run_cli("search", "proposal", "--folder-id", "9", "--limit", "1", "--offset", str(first["next_offset"]))
        self.assertTrue(second["complete"])
        self.assertEqual({first["entries"][0]["id"], second["entries"][0]["id"]}, {"1", "2"})
        approved = self.run_cli("read-file", "1", "--text")
        draft = self.run_cli("read-file", "2", "--text")
        self.assertIn("24000", approved["extraction"]["text"])
        self.assertIn("UNAPPROVED", draft["extraction"]["text"])
        self.assertEqual(approved["version"]["file_version_id"], "11")
        brief = self.root / "brief.md"
        brief.write_text("Approved: USD 24000, six weeks. Source: https://app.box.com/file/1, version 11. Draft differs; not approved.")
        saved = self.run_cli("save-document", str(brief), "--parent-id", "10")
        self.assertTrue(saved["verification"]["content_readback_match"])
        self.assertTrue(saved["verified"])
        readback = self.run_cli("read-file", saved["id"], "--text")
        self.assertEqual(readback["extraction"]["text"], brief.read_text())
        self.assertEqual(json.loads(self.state.read_text())["posts"], 1)

    def test_contract_source_preserves_term_and_notice(self):
        out = self.run_cli("read-file", "3", "--text")
        self.assertIn("December 31, 2027", out["extraction"]["text"])
        self.assertIn("October 2, 2027", out["extraction"]["text"])
        self.assertEqual(out["source_url"], "https://app.box.com/file/3")

    def test_denied_save_does_not_create_file(self):
        state = json.loads(self.state.read_text()); state["deny_upload"] = True
        self.state.write_text(json.dumps(state))
        p = self.root / "brief.md"; p.write_text("synthetic")
        out = self.run_cli("save-document", str(p), "--parent-id", "10", expected=1)
        self.assertEqual(out["status"], 403)
        self.assertEqual(json.loads(self.state.read_text()).get("posts", 0), 0)

    def run_workflow(self, *args, expected=0):
        proc = subprocess.run([sys.executable, str(ROOT / "bin" / "boxwork"), *args],
                              env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, expected, proc.stderr + proc.stdout)
        return json.loads(proc.stdout)

    def test_customer_workflow_uses_actual_read_path(self):
        result = self.run_workflow("gather-customer-files", "--folder-id", "9",
                                   "--customer", "Synthetic", "--alias", "USD 24000")
        self.assertTrue(result["coverage"]["complete"])
        self.assertEqual([f["file_id"] for f in result["confirmed_files"]], ["1"])

    def test_contract_workflow_separates_notice_and_expiry(self):
        result = self.run_workflow("review-contracts", "--folder-id", "9", "--year", "2027", expected=2)
        self.assertEqual(result["expiring_in_year"], [])
        self.assertTrue(result["evidence_only"])
        contract = result["candidate_expirations"][0]
        self.assertTrue(contract["requires_review"])
        self.assertEqual(contract["expiration_date"], "2027-12-31")
        self.assertEqual(contract["notice_dates"], ["2027-10-02"])
        self.assertTrue(contract["signals"]["auto_renewal_indicated"])

    def test_bad_pagination_rejected_before_transport(self):
        for args in [("--limit", "0"), ("--offset", "-1"), ("--offset", "10000")]:
            out = self.run_cli("list-folder", "9", *args, expected=1)
            self.assertFalse(out["ok"])


if __name__ == "__main__":
    unittest.main()
