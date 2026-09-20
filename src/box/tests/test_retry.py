#!/usr/bin/env python3
"""Unit tests for retry/error helpers in the box CLI. No network use."""

import importlib.util
import importlib.machinery
import sys
from pathlib import Path

loader = importlib.machinery.SourceFileLoader(
    "boxcli", str(Path(__file__).resolve().parents[1] / "bin" / "box"))
SPEC = importlib.util.spec_from_loader("boxcli", loader)
boxcli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(boxcli)


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        sys.exit(1)


# classify_retry(status, attempt, mutating)
check("GET retries on 429 attempt 1", boxcli.classify_retry(429, 1, False) is True)
check("GET retries on 503 attempt 2", boxcli.classify_retry(503, 2, False) is True)
check("GET no retry on 400", boxcli.classify_retry(400, 1, False) is False)
check("GET no retry on 404", boxcli.classify_retry(404, 1, False) is False)
check("no retry past max attempts", boxcli.classify_retry(500, 3, False) is False)
check("no retry on 200", boxcli.classify_retry(200, 1, False) is False)
check("POST never retried on timeout", boxcli.classify_retry(0, 1, True) is False)
check("POST never retried on 500", boxcli.classify_retry(500, 1, True) is False)
check("POST never retried on 502 attempt 2", boxcli.classify_retry(502, 2, True) is False)

d = boxcli.backoff_delay(1, "2")
check("honors Retry-After", d == 2.0)
d = boxcli.backoff_delay(1, None)
check("backoff grows", boxcli.backoff_delay(2, None) > d)
check("backoff capped", boxcli.backoff_delay(10, None) <= 8.0)

e = boxcli.actionable_error(404, b'{"x":1}', "get_file")
check("404 hint mentions ID", "ID" in e["hint"] and e["ok"] is False)
e = boxcli.actionable_error(401, b'{}', "identity")
check("401 hint is diagnostic, no auto-reconnect", "credential" in e["hint"] and "reconnect" in e["hint"].lower())
e = boxcli.actionable_error(409, b'{}', "create_folder")
check("409 hint mentions exists", "exists" in e["hint"])

s = boxcli.slim_entry({"id": "1", "type": "file", "name": "a",
                       "sha1": "abc", "size": 5, "file_version": {"id": "9"}})
check("slim file url", s["source_url"] == "https://app.box.com/file/1")
check("slim version", s["version"]["file_version_id"] == "9")
s = boxcli.slim_entry({"id": "2", "type": "folder", "name": "b"})
check("slim folder url", s["source_url"] == "https://app.box.com/folder/2")

r = boxcli.extract_text(b"hello", "text/markdown", "x.md")
check("text extraction ok", r["status"] == "ok" and r["text"] == "hello")

check("valid id", boxcli.valid_id("123456789012") is True)
check("invalid id rejected", boxcli.valid_id("abc") is False)
ok, _ = boxcli.validate_filename("a/b")
check("slash in filename rejected", ok is False)
ok, _ = boxcli.validate_filename("ok-name.md")
check("good filename accepted", ok is True)

print("ALL UNIT TESTS PASSED")
