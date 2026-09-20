#!/usr/bin/env python3
"""Regression tests for the box CLI: full request paths with mocked transport,
uncertain-write reconciliation, extraction statuses, URL redaction, malformed
inputs, and version-change detection. No network use.

Synthetic PDF/DOCX extraction is tested LOCALLY here; that is distinct from
live-download proof against Box (see the sanitized test receipt).
"""

import argparse
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import os
import zipfile

BIN = str(Path(__file__).resolve().parents[1] / "bin" / "box")
loader = importlib.machinery.SourceFileLoader("boxcli", BIN)
SPEC = importlib.util.spec_from_loader("boxcli", loader)
boxcli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(boxcli)

PASS_COUNT = 0


def check(name, cond, extra=""):
    global PASS_COUNT
    status = "PASS " if cond else "FAIL "
    print(status + name + ((" | " + str(extra)[:160]) if extra and not cond else ""))
    if cond:
        PASS_COUNT += 1
    else:
        sys.exit(1)


class DummyReq:
    def __init__(self, url):
        self.full_url = url

    def add_header(self, *a):
        pass


class FakeTransport:
    """Dispatch fake responses by URL substring. Records call counts."""

    def __init__(self):
        self.routes = []  # (substring, handler)
        self.calls = []

    def add(self, substring, handler):
        self.routes.append((substring, handler))

    def open(self, req, timeout):
        url = req.full_url
        self.calls.append(("open", url))
        for sub, handler in self.routes:
            if sub in url:
                return handler(url)
        raise AssertionError("no fake route for " + url)

    def follow(self, req, timeout):
        url = req.full_url
        self.calls.append(("follow", url))
        for sub, handler in self.routes:
            if sub in url:
                return handler(url)
        raise AssertionError("no fake follow route for " + url)

    def count(self, kind, substring):
        return sum(1 for k, u in self.calls if k == kind and substring in u)


def install(fake):
    boxcli.build_request = lambda url, method="GET", data=None, content_type=None: DummyReq(url)
    boxcli._http_open = fake.open
    boxcli._follow_open = fake.follow
    boxcli.backoff_delay = lambda attempt, ra: 0


def json_resp(obj, status=200, ctype="application/json"):
    return (status, json.dumps(obj).encode(), {"Content-Type": ctype})


def meta(file_id, version="v1", sha1="a" * 40, size=4, name="f.md", parent="9"):
    return {"id": file_id, "type": "file", "name": name, "size": size, "sha1": sha1,
            "file_version": {"id": version}, "parent": {"id": parent, "name": "p"},
            "modified_at": "2026-01-01T00:00:00Z"}


# --- 1. mutating POST is never retried on timeout -------------------------
fake = FakeTransport()
calls = {"n": 0}


def boom(url):
    calls["n"] += 1
    raise TimeoutError("simulated response loss")


fake.add("/folders", boom)
install(fake)
st, body, hdrs = boxcli.do_request("https://api.box.com/2.0/folders",
                                   method="POST", data=b"{}", mutating=True)
check("POST timeout -> status 0, exactly one attempt", st == 0 and calls["n"] == 1,
      f"status={st} attempts={calls['n']}")

# --- 2. idempotent GET retries on 500 then succeeds ------------------------
fake = FakeTransport()
seq = {"n": 0}


def flaky(url):
    seq["n"] += 1
    if seq["n"] < 3:
        raise boxcli.urllib.error.HTTPError(url, 500, "err", {}, io.BytesIO(b"{}"))
    return json_resp({"ok": True})


fake.add("/folders/1/items", flaky)
install(fake)
st, body, hdrs = boxcli.do_request("https://api.box.com/2.0/folders/1/items",
                                   mutating=False)
check("GET retried on 500, succeeded on 3rd try", st == 200 and seq["n"] == 3,
      f"status={st} attempts={seq['n']}")

# --- 3. create-folder ambiguous -> existing folder, creation unattributed -------------------
fake = FakeTransport()


def post_boom(url):
    raise TimeoutError("simulated response loss")


def items_one(url):
    return json_resp({"total_count": 1, "entries": [
        {"id": "777", "type": "folder", "name": "reconciled",
         "file_version": None}]})


fake.add("/items", items_one)                # GET reconcile lookup
fake.add("/2.0/folders", post_boom)          # POST create
install(fake)
buf = io.StringIO()
old = sys.stdout
sys.stdout = buf
rc = boxcli.cmd_create_folder(argparse.Namespace(name="reconciled", parent_id="42"))
sys.stdout = old
out = json.loads(buf.getvalue())
check("create-folder timeout reconciled: ambiguous, creation unattributed",
      rc == 2 and out.get("ambiguous") is True
      and out["reconciliation"]["outcome"] == "exists_unattributed"
      and out["reconciliation"]["folder"]["id"] == "777", json.dumps(out)[:200])
check("create POST attempted exactly once",
      sum(1 for k, u in fake.calls
          if k == "open" and u == "https://api.box.com/2.0/folders") == 1)

# --- 4. save-document ambiguous -> checksum match -> metadata match only -------------
fake = FakeTransport()
content = b"reconciled-bytes"
csha = hashlib.sha1(content).hexdigest()
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
tmp.write(content)
tmp.close()


def up_boom(url):
    raise TimeoutError("simulated response loss")


def items_file(url):
    return json_resp({"total_count": 1, "entries": [
        {"id": "888", "type": "file", "name": os.path.basename(tmp.name),
         "sha1": csha, "size": len(content),
         "file_version": {"id": "fv1"}}]})


def meta_match(url):
    return json_resp({"id": "888", "type": "file", "name": "x", "sha1": csha,
                      "size": len(content), "parent": {"id": "42"},
                      "file_version": {"id": "fv1"}})


fake.add("/files/content", up_boom)
fake.add("/items", items_file)
fake.add("/files/888", meta_match)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_save_document(argparse.Namespace(local_path=tmp.name,
                                                 parent_id="42", name=None))
sys.stdout = old
out = json.loads(buf.getvalue())
check("save-document timeout reconciled: checksum match -> metadata match only",
      rc == 2 and out["ambiguous"] is True
      and out["reconciliation"]["outcome"] == "metadata_match", json.dumps(out)[:200])

# --- 5. save-document ambiguous -> checksum mismatch -> conflict ----------
fake = FakeTransport()


def items_other(url):
    return json_resp({"total_count": 1, "entries": [
        {"id": "889", "type": "file", "name": os.path.basename(tmp.name),
         "sha1": "0" * 40, "size": 999, "file_version": {"id": "fv9"}}]})


fake.add("/files/content", up_boom)
fake.add("/items", items_other)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_save_document(argparse.Namespace(local_path=tmp.name,
                                                 parent_id="42", name=None))
sys.stdout = old
out = json.loads(buf.getvalue())
check("save-document timeout reconciled: checksum mismatch -> conflict",
      out["reconciliation"]["outcome"] == "conflict")
os.unlink(tmp.name)

# --- 6. PNG bytes are NOT marked as successful text -----------------------
r = boxcli.extract_text(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "image/png", "a.png")
check("PNG extraction -> unsupported, not ok",
      r["status"] == "unsupported" and "text" not in r, json.dumps(r))

# --- 7. synthetic DOCX: entities decoded, paragraphs kept, limits noted ---
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
doc_xml = (
    '<w:document xmlns:w="%s"><w:body>'
    '<w:p><w:r><w:t>A &amp; B</w:t></w:r></w:p>'
    '<w:p><w:r><w:t>Second</w:t></w:r><w:r><w:t xml:space="preserve"> para</w:t></w:r></w:p>'
    '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>cell1</w:t></w:r></w:p></w:tc>'
    '<w:tc><w:p><w:r><w:t>cell2</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
    '</w:body></w:document>' % W).encode()
hdr_xml = ('<w:hdr xmlns:w="%s"><w:p><w:r><w:t>Header secret</w:t></w:r></w:p>'
           '</w:hdr>' % W).encode()
bufx = io.BytesIO()
with zipfile.ZipFile(bufx, "w") as zf:
    zf.writestr("[Content_Types].xml", "<Types/>")
    zf.writestr("word/document.xml", doc_xml)
    zf.writestr("word/header1.xml", hdr_xml)
docx_bytes = bufx.getvalue()
r = boxcli.extract_text(docx_bytes,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "test.docx")
check("DOCX entity decoded to 'A & B'",
      r["status"] == "partial" and "A & B" in r["text"], r["text"][:120])
check("DOCX paragraph boundaries kept",
      "Second para" in r["text"] and r["text"].index("Second para") > r["text"].index("A & B"))
check("DOCX header excluded, limits disclosed",
      "Header secret" not in r["text"]
      and any("header" in lim.lower() for lim in r["limits"]))

# --- 8. synthetic PDF via locally built minimal PDF -----------------------
def make_pdf(text):
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        None,  # stream placeholder
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    stream = f"BT /F1 24 Tf 72 720 Td ({text}) Tj ET".encode()
    objs[3] = "<< /Length %d >>\nstream\n" % len(stream)
    out = b"%PDF-1.4\n"
    offs = []
    for i, body in enumerate(objs, start=1):
        offs.append(len(out))
        out += f"{i} 0 obj\n".encode()
        if i == 4:
            out += body.encode() + stream + b"\nendstream\n"
        else:
            out += body.encode() + b"\n"
        out += b"endobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode() + b"0000000000 65535 f \n"
    for o in offs:
        out += f"{o:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF").encode()
    return out


pdf_bytes = make_pdf("Hello synthetic PDF 123")
r = boxcli.extract_text(pdf_bytes, "application/pdf", "t.pdf")
check("synthetic PDF text extracted locally",
      r["status"] == "ok" and "Hello synthetic PDF 123" in r["text"],
      r.get("text", "")[:80] + " status=" + r["status"])

# --- 9. redirect redaction ------------------------------------------------
fake = FakeTransport()


def redir(url):
    raise boxcli.RedirectEncountered(
        "https://dl.boxcloud.com/d/1/abc?sig=S3CR3T-TOKEN", 302)


def follow_ok(url):
    return (200, b"data-bytes", {"Content-Type": "text/plain"})


fake.add("/content", redir)
fake.add("dl.boxcloud.com", follow_ok)
install(fake)
ok, res = boxcli.download_content("555")
blob = json.dumps({k: v for k, v in res.items() if k != "bytes"})
check("signed URL redacted: host only, no token material",
      ok is True and res["redirect_host"] == "dl.boxcloud.com"
      and "S3CR3T" not in blob and "sig=" not in blob, blob[:160])


def redir_http(url):
    raise boxcli.RedirectEncountered("http://dl.boxcloud.com/x", 302)


fake2 = FakeTransport()
fake2.add("/content", redir_http)
install(fake2)
ok, res = boxcli.download_content("555")
check("non-HTTPS redirect refused",
      ok is False and "HTTPS" in res.get("reason", ""), json.dumps(res)[:160])


def redir_evil(url):
    raise boxcli.RedirectEncountered("https://evil.example.com/x?token=abc123", 302)


fake3 = FakeTransport()
fake3.add("/content", redir_evil)
install(fake3)
ok, res = boxcli.download_content("555")
blob = json.dumps(res)
check("unknown host refused, host-only, token redacted",
      ok is False and res.get("refused_redirect_host") == "evil.example.com"
      and "abc123" not in blob and "token=" not in blob, blob[:160])

# --- 10. malformed inputs: no network touched -----------------------------
fake = FakeTransport()
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_get_file(argparse.Namespace(file_id="abc"))
sys.stdout = old
out = json.loads(buf.getvalue())
check("non-numeric file id rejected without network",
      rc == 1 and out["ok"] is False and fake.calls == [], json.dumps(out)[:120])

proc = subprocess.run([BIN, "save-document", "/tmp/x", "--parent-id", "0",
                       "--name", "a/b"], capture_output=True, text=True)
check("slash in filename rejected at CLI",
      proc.returncode == 1 and "invalid file name" in proc.stdout)

proc = subprocess.run([BIN, "create-folder", "n", "--parent-id", "xyz"],
                      capture_output=True, text=True)
check("non-numeric parent id rejected at CLI",
      proc.returncode == 1 and "numeric" in proc.stdout)

# --- 11. version change during read is detected ---------------------------
fake = FakeTransport()
meta_calls = {"n": 0}


def meta_v(url):
    meta_calls["n"] += 1
    v = "fv-before" if meta_calls["n"] == 1 else "fv-after"
    return json_resp(meta("999", version=v, sha1=hashlib.sha1(b"hello").hexdigest(),
                          size=5, name="n.txt"))


def dl_ok(url):
    return (200, b"hello", {"Content-Type": "text/plain"})


fake.add("/files/999?", meta_v)
fake.add("/files/999/content", dl_ok)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_read_file(argparse.Namespace(file_id="999", out=None, text=True))
sys.stdout = old
out = json.loads(buf.getvalue())
check("concurrent version change detected",
      out["version_changed_during_read"] is True and "warning" in out
      and out["version"]["file_version_id"] == "fv-before"
      and out["version"]["verified"] is True,
      json.dumps({k: out.get(k) for k in ("version_changed_during_read", "warning")})[:160])

# --- 12. failed extraction -> ok false, explicit completeness -------------
fake = FakeTransport()
png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def meta_png(url):
    return json_resp(meta("1000", sha1=hashlib.sha1(png).hexdigest(),
                          size=len(png), name="a.png"))


def dl_png(url):
    return (200, png, {"Content-Type": "image/png"})


fake.add("/files/1000?", meta_png)
fake.add("/files/1000/content", dl_png)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_read_file(argparse.Namespace(file_id="1000", out=None, text=True))
sys.stdout = old
out = json.loads(buf.getvalue())
check("unsupported extraction -> ok false with explicit status",
      rc == 1 and out["ok"] is False
      and out["extraction"]["status"] == "unsupported"
      and out["source_url"] == "https://app.box.com/file/1000", json.dumps(out)[:200])

# --- 13. long text: explicit truncation, no silent cut --------------------
fake = FakeTransport()
big = ("x" * 25000).encode()


def meta_big(url):
    return json_resp(meta("1001", sha1=hashlib.sha1(big).hexdigest(),
                          size=len(big), name="big.txt"))


def dl_big(url):
    return (200, big, {"Content-Type": "text/plain"})


fake.add("/files/1001?", meta_big)
fake.add("/files/1001/content", dl_big)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_read_file(argparse.Namespace(file_id="1001", out=None, text=True))
sys.stdout = old
out = json.loads(buf.getvalue())
ex = out["extraction"]
check("long text: truncated flag + total_length, no silent cut",
      rc == 0 and ex["truncated"] is True and ex["total_length"] == 25000
      and len(ex["text"]) == boxcli.TEXT_PREVIEW_LIMIT
      and out["download"]["complete"] is True)

# --- 14. nested JSON error secrets are sanitized ------------------------
err = boxcli.actionable_error(
    403,
    b'{"context_info": {"url": "https://dl.boxcloud.com/d/SYNTHETIC_SECRET_123"},'
    b' "message": "denied, see https://x.example/a?b=1", "nested": [{"deep": "https://y.example/?t=2"}]}',
    "get_file")
blob = json.dumps(err)
check("parsed JSON error: signed URL redacted, nested secrets sanitized",
      "SYNTHETIC_SECRET_123" not in blob
      and err["detail"]["context_info"]["url"] == "[redacted]"
      and "https://x.example" not in blob and "https://y.example" not in blob
      and err["ok"] is False, blob[:220])

# full request path: 404 body carrying a signed URL in JSON (in-process, mocked)
fake = FakeTransport()


def notfound_secret(url):
    raise boxcli.urllib.error.HTTPError(
        url, 404, "nf", {},
        io.BytesIO(b'{"context_info": {"url": "https://dl.boxcloud.com/d/NESTED_SECRET_456"}}'))


fake.add("/files/4242", notfound_secret)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_get_file(argparse.Namespace(file_id="4242"))
sys.stdout = old
out_text = buf.getvalue()
check("full-path 404 output carries no nested secret",
      rc == 1 and "NESTED_SECRET_456" not in out_text
      and "[redacted]" in out_text, out_text[:200])

# --- 15. read-file checksum mismatch -> unverified, nonzero exit, no --out
fake = FakeTransport()
wrong = b"wrong"


def meta_zero(url):
    return json_resp(meta("2000", sha1="0" * 40, size=len(wrong), name="w.txt"))


def dl_wrong(url):
    return (200, wrong, {"Content-Type": "text/plain"})


fake.add("/files/2000?", meta_zero)
fake.add("/files/2000/content", dl_wrong)
install(fake)
outpath = tempfile.mktemp(suffix=".out")
if os.path.exists(outpath):
    os.unlink(outpath)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_read_file(argparse.Namespace(file_id="2000", out=outpath, text=False))
sys.stdout = old
out = json.loads(buf.getvalue())
check("checksum mismatch -> ok false, version not verified, no --out write",
      rc == 1 and out["ok"] is False
      and out["version"]["verified"] is False
      and "checksum" in out["error"]
      and not os.path.exists(outpath), json.dumps(out)[:200])

# --- 16. read-file size mismatch -> error ---------------------------------
fake = FakeTransport()


def meta_bigsize(url):
    return json_resp(meta("2001", sha1=hashlib.sha1(b"short").hexdigest(),
                          size=100, name="s.txt"))


def dl_short(url):
    return (200, b"short", {"Content-Type": "text/plain"})


fake.add("/files/2001?", meta_bigsize)
fake.add("/files/2001/content", dl_short)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_read_file(argparse.Namespace(file_id="2001", out=None, text=True))
sys.stdout = old
out = json.loads(buf.getvalue())
check("size mismatch -> ok false with size error",
      rc == 1 and out["ok"] is False and "size mismatch" in out["error"],
      json.dumps(out)[:160])

# --- 17. read-file metadata missing sha1 -> cannot verify -----------------
fake = FakeTransport()


def meta_nosha(url):
    m = meta("2002", sha1=None, size=5, name="n.txt")
    m["sha1"] = None
    return json_resp(m)


def dl_five(url):
    return (200, b"12345", {"Content-Type": "text/plain"})


fake.add("/files/2002?", meta_nosha)
fake.add("/files/2002/content", dl_five)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_read_file(argparse.Namespace(file_id="2002", out=None, text=True))
sys.stdout = old
out = json.loads(buf.getvalue())
check("missing metadata sha1 -> unverified error",
      rc == 1 and out["ok"] is False
      and "cannot be verified" in out["error"], json.dumps(out)[:160])

# --- 18. after-metadata failure -> version check degraded, still ok -------
fake = FakeTransport()
good = b"good!"


def meta_before(url):
    return json_resp(meta("2003", sha1=hashlib.sha1(good).hexdigest(),
                          size=len(good), name="g.txt"))


calls18 = {"n": 0}


def meta_maybe(url):
    calls18["n"] += 1
    if calls18["n"] == 1:
        return meta_before(url)
    raise boxcli.urllib.error.HTTPError(url, 500, "err", {}, io.BytesIO(b"{}"))


def dl_good(url):
    return (200, good, {"Content-Type": "text/plain"})


fake.add("/files/2003?", meta_maybe)
fake.add("/files/2003/content", dl_good)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_read_file(argparse.Namespace(file_id="2003", out=None, text=True))
sys.stdout = old
out = json.loads(buf.getvalue())
check("after-metadata failure: version_changed null, checksum still verifies",
      rc == 0 and out["ok"] is True
      and out["version_changed_during_read"] is None
      and out["version"]["verified"] is True
      and "version_check_note" in out, json.dumps(out)[:200])

# --- 19. save-document readback mismatch -> ok false ----------------------
fake = FakeTransport()
up_bytes = b"upload-me"
up_sha = hashlib.sha1(up_bytes).hexdigest()
tmp2 = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
tmp2.write(up_bytes)
tmp2.close()


def up_accepted(url):
    return json_resp({"total_count": 1,
                      "entries": [{"id": "900", "type": "file",
                                   "name": os.path.basename(tmp2.name)}]}, status=201)


def meta_wrongsha(url):
    return json_resp({"id": "900", "type": "file", "name": "x",
                      "sha1": "f" * 40, "size": len(up_bytes),
                      "parent": {"id": "42"}, "file_version": {"id": "fvx"}})


fake.add("/files/content", up_accepted)
fake.add("/files/900", meta_wrongsha)
install(fake)
buf = io.StringIO()
sys.stdout = buf
rc = boxcli.cmd_save_document(argparse.Namespace(local_path=tmp2.name,
                                                 parent_id="42", name=None))
sys.stdout = old
out = json.loads(buf.getvalue())
check("save readback mismatch -> ok false, ambiguous, exit 2",
      rc == 2 and out["ok"] is False and out["verified"] is False
      and out["ambiguous"] is True, json.dumps(out)[:200])
os.unlink(tmp2.name)

print(f"ALL {PASS_COUNT} REGRESSION TESTS PASSED")
