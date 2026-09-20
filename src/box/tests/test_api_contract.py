"""Box contract regressions. Synthetic transport; never contacts Box or authd."""
import argparse
import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import urllib.error

BIN = Path(__file__).resolve().parents[1] / "bin" / "box"
stub = types.ModuleType("dynamic_credentials")
stub.add_surrogate_to_request = lambda req, *a, **kw: req.add_header("Authorization", "Bearer hsurr:test")
stub.read_response_body = lambda response: response.read()
sys.modules["dynamic_credentials"] = stub
loader = importlib.machinery.SourceFileLoader("contract_box", str(BIN))
spec = importlib.util.spec_from_loader(loader.name, loader)
box = importlib.util.module_from_spec(spec)
loader.exec_module(box)


def invoke(func, **kw):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = func(argparse.Namespace(**kw))
    return code, json.loads(output.getvalue())


def response(value, status=200):
    return status, json.dumps(value).encode(), {}


class ContractTests(unittest.TestCase):
    def test_retry_after_does_not_retry_early(self):
        self.assertGreaterEqual(box.backoff_delay(1, "100"), 100)

    def test_retry_after_http_date(self):
        with patch.object(box.time, "time", return_value=0):
            self.assertEqual(box.backoff_delay(1, "Thu, 01 Jan 1970 00:01:40 GMT"), 100)

    def test_short_lowercase_retry_after_waits(self):
        error = urllib.error.HTTPError("https://api.box.com/2.0/users/me", 429, "rate", {"retry-after": "3"}, io.BytesIO(b"{}"))
        self.addCleanup(error.close)
        with patch.object(box, "_http_open", side_effect=[error, (200, b"{}", {})]), patch.object(box.time, "sleep") as sleep:
            status, _, _ = box.do_request(box.API_BASE + "/users/me")
        self.assertEqual(status, 200)
        sleep.assert_called_once_with(3)

    def test_long_lowercase_retry_after_returns_without_early_retry(self):
        error = urllib.error.HTTPError("https://api.box.com/2.0/users/me", 429, "rate", {"retry-after": "100"}, io.BytesIO(b"{}"))
        self.addCleanup(error.close)
        with patch.object(box, "_http_open", side_effect=error) as opened, patch.object(box.time, "sleep") as sleep:
            status, body, _ = box.do_request(box.API_BASE + "/users/me")
        self.assertEqual(status, 429)
        self.assertEqual(json.loads(body)["retry_after_seconds"], 100)
        self.assertEqual(opened.call_count, 1)
        sleep.assert_not_called()

    def test_sparse_pagination_uses_response_limit(self):
        offsets = []
        def request(url):
            query = box.urllib.parse.parse_qs(box.urllib.parse.urlparse(url).query)
            offset = int(query["offset"][0]); offsets.append(offset)
            pages = {0: {"entries": [], "offset": 0, "limit": 2, "total_count": 3},
                     2: {"entries": [{"id": "7", "type": "folder", "name": "target"}], "offset": 2, "limit": 2, "total_count": 3}}
            return response(pages.get(offset, {"entries": [], "offset": offset, "limit": 2, "total_count": 3}))
        with patch.object(box, "do_request", side_effect=request):
            ok, matches, _ = box.find_in_folder("9", "target", "folder")
        self.assertTrue(ok)
        self.assertEqual(offsets, [0, 2])
        self.assertEqual([m["id"] for m in matches], ["7"])

    def test_missing_total_is_not_complete(self):
        with patch.object(box, "do_request", return_value=response({"entries": []})):
            _, out = invoke(box.cmd_search, query="proposal", folder_id="9", limit=2, offset=0)
        self.assertFalse(out["complete"])

    def test_pagination_repeated_offset_stops(self):
        pages = [response({"entries": [], "offset": 0, "limit": 2, "total_count": 5}),
                 response({"entries": [], "offset": 0, "limit": 2, "total_count": 5})]
        with patch.object(box, "do_request", side_effect=pages) as request:
            ok, _, _ = box.find_in_folder("9", "target", "folder")
        self.assertFalse(ok)
        self.assertEqual(request.call_count, 2)

    def test_sparse_terminal_page_is_complete(self):
        page = box.page_state({"entries": [], "offset": 2, "limit": 2, "total_count": 3}, 2, 2)
        self.assertTrue(page["complete"])
        self.assertIsNone(page["next_offset"])

    def test_id_rejects_newline(self):
        self.assertFalse(box.valid_id("123\n"))

    def test_redirect_credentials_or_nonstandard_port_refused(self):
        for url in ["https://user:password@dl.boxcloud.com/file", "https://dl.boxcloud.com:444/file"]:
            with patch.object(box, "do_request", return_value=(302, b"", {"location": url})), patch.object(box, "_follow_open") as follow:
                ok, _ = box.download_content("7")
            self.assertFalse(ok)
            follow.assert_not_called()

    def test_empty_pdf_does_not_claim_readable_text(self):
        completed = types.SimpleNamespace(returncode=0, stdout=b"\x0c", stderr=b"")
        with patch.object(box.subprocess, "run", return_value=completed):
            extracted = box.extract_text(b"synthetic-pdf", "application/pdf", "scan.pdf")
        self.assertNotEqual(extracted["status"], "ok")

    def test_definitive_folder_denial_never_reconciles(self):
        with patch.object(box, "do_request", return_value=response({}, 403)), patch.object(box, "reconcile_create_folder", return_value={"outcome": "unknown"}) as reconcile:
            code, out = invoke(box.cmd_create_folder, name="new", parent_id="9")
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], 403)
        reconcile.assert_not_called()

    def test_existing_folder_does_not_prove_creation(self):
        with patch.object(box, "find_in_folder", return_value=(True, [{"id": "7"}], "complete")):
            result = box.reconcile_create_folder("9", "new")
        self.assertNotEqual(result["outcome"], "created")

    def test_zero_size_mismatch_is_incomplete(self):
        meta = {"id": "7", "name": "empty.txt", "size": 0, "sha1": hashlib.sha1(b"").hexdigest(), "file_version": {"id": "8"}}
        with patch.object(box, "get_metadata", return_value=response(meta)), patch.object(box, "download_content", return_value=(True, {"bytes": b"unexpected", "content_type": "text/plain"})):
            code, out = invoke(box.cmd_read_file, file_id="7", text=True, out=None)
        self.assertEqual(code, 1)
        self.assertFalse(out["download"]["complete"])

    def test_missing_version_is_not_verified(self):
        data = b"hello"
        meta = {"id": "7", "name": "a.txt", "size": len(data), "sha1": hashlib.sha1(data).hexdigest()}
        with patch.object(box, "get_metadata", return_value=response(meta)), patch.object(box, "download_content", return_value=(True, {"bytes": data, "content_type": "text/plain"})):
            code, out = invoke(box.cmd_read_file, file_id="7", text=True, out=None)
        self.assertEqual(code, 1)
        self.assertFalse(out["version"]["verified"])

    def test_upload_requires_content_readback(self):
        data = b"brief"
        meta = {"id": "7", "name": "brief.md", "size": len(data), "sha1": hashlib.sha1(data).hexdigest(), "parent": {"id": "9"}, "file_version": {"id": "8"}}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "brief.md"; p.write_bytes(data)
            with patch.object(box, "do_request", return_value=response({"entries": [{"id": "7", "name": p.name}]}, 201)), patch.object(box, "get_metadata", return_value=response(meta)), patch.object(box, "download_content", return_value=(True, {"bytes": b"wrong"})) as download:
                code, out = invoke(box.cmd_save_document, local_path=str(p), parent_id="9", name=None)
        download.assert_called_once_with("7")
        self.assertFalse(out["verified"])
        self.assertNotEqual(code, 0)

    def test_invalid_utf8_is_not_clean_extraction(self):
        result = box.extract_text(b"bad\xfftext", "text/plain", "a.txt")
        self.assertNotEqual(result["status"], "ok")


if __name__ == "__main__":
    unittest.main()
