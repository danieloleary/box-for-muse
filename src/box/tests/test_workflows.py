#!/usr/bin/env python3
"""Offline acceptance fixtures for the boxwork enterprise workflows (v5).

Synthetic data only; the fake cli substitutes for bin/box transport, so no
network is used. Regression cases for the five independent-review failures:

  1. root with child folder containing customer file -> file found via traversal
  2. denied child folder -> coverage.complete false with the folder in gaps
  3. "Cedar Workshop" must not confirm for alias "Cedar Works" (+case CW-104);
     alias and case together must both match with boundaries
  4. contract max_files=1 with two files -> coverage.complete false
  5. base expiring 2027 + amendment to 2028 -> base to needs_review with both
     sources, never a stale definitive 2027 expiration

Plus: truncated extraction, invalid calendar dates, cycle dedupe, generic
filenames via bounded verified content evidence, alias-OR, input validation.
"""

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse, parse_qs

loader = importlib.machinery.SourceFileLoader(
    "workflows", str(Path(__file__).resolve().parents[1] / "workflows.py"))
SPEC = importlib.util.spec_from_loader("workflows", loader)
wf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wf)

PASS_COUNT = 0


def check(name, cond, extra=""):
    global PASS_COUNT
    print(("PASS " if cond else "FAIL ") + name +
          ((" | " + str(extra)[:220]) if extra and not cond else ""))
    if cond:
        PASS_COUNT += 1
    else:
        sys.exit(1)


def entry(fid, name, ftype="file"):
    return {"id": fid, "type": ftype, "name": name,
            "file_version": {"id": "fv-" + fid}, "sha1": "s" + fid, "size": 10}


class FakeCli:
    API_BASE = "https://api.box.com/2.0"

    def __init__(self):
        self.pages = {}        # folder_id -> list of pages
        self.fail_folders = set()
        self.texts = {}        # file_id -> (rc, text, verified, truncated)

    @staticmethod
    def valid_id(v):
        import re as _re
        return bool(_re.match(r"^[0-9]+$", v or ""))

    def do_request(self, url):
        parts = urlparse(url)
        fid = parts.path.split("/folders/")[1].split("/items")[0]
        if fid in self.fail_folders:
            return 403, b"{}", {}
        q = parse_qs(parts.query)
        limit, offset = int(q["limit"][0]), int(q["offset"][0])
        pages = self.pages.get(fid, [])
        idx = offset // limit
        entries = pages[idx] if idx < len(pages) else []
        total = sum(len(p) for p in pages)
        return 200, json.dumps({"total_count": total,
                                "entries": entries}).encode(), {}

    def cmd_read_file(self, args):
        rc, text, verified, truncated = self.texts.get(args.file_id,
                                                       (1, None, False, False))
        if rc != 0 or text is None:
            print(json.dumps({"ok": False, "action": "read_file",
                              "hint": "synthetic unreadable"}))
            return 1
        print(json.dumps({
            "ok": True, "id": args.file_id,
            "version": {"file_version_id": "fv-" + args.file_id,
                        "sha1": "s" + args.file_id, "size": len(text),
                        "verified": verified},
            "extraction": {"status": "ok" if not truncated else "partial",
                            "format": "md", "text": text,
                            "total_length": len(text), "truncated": truncated}}))
        return 0


def cust(name, aliases=(), cases=()):
    return {"name": name, "aliases": list(aliases), "cases": list(cases)}


# ---------------- failure 1: child folder traversal ----------------
cli = FakeCli()
cli.pages["1"] = [[entry("10", "Customer Files", "folder")]]
cli.pages["10"] = [[entry("101", "Cedar Works CW-104 proposal.md")]]
cli.texts["101"] = (0, "x", True, False)

res = wf.gather_customer_files(cli, "1",
                               [cust("Cedar Works", ["Cedar Works"], ["CW-104"])])
check("f1: child folder traversed, file confirmed",
      res["ok"] and [f["file_id"] for f in res["confirmed_files"]] == ["101"]
      and res["coverage"]["complete"] is True, res)
check("f1: folder context recorded",
      res["confirmed_files"][0]["folder_path"] == ["folder:1", "Customer Files"],
      res["confirmed_files"][0]["folder_path"])

# ---------------- failure 2: denied child folder ----------------
cli2 = FakeCli()
cli2.pages["1"] = [[entry("10", "Customer Files", "folder"),
                    entry("11", "Locked", "folder")]]
cli2.pages["10"] = [[entry("101", "Cedar Works CW-104 proposal.md")]]
cli2.fail_folders = {"11"}
cli2.texts["101"] = (0, "x", True, False)

res2 = wf.gather_customer_files(cli2, "1",
                                [cust("Cedar Works", ["Cedar Works"], ["CW-104"])])
check("f2: denied child folder -> coverage incomplete",
      res2["coverage"]["complete"] is False, res2["coverage"])
check("f2: gap names the inaccessible folder",
      any(g.get("folder_id") == "11" and g.get("status") == 403
          for g in res2["coverage"]["gaps"]), res2["coverage"]["gaps"])
check("f2: accessible files still returned",
      [f["file_id"] for f in res2["confirmed_files"]] == ["101"])

# ---------------- failure 3: boundaries + both-must-match ----------------
cli3 = FakeCli()
cli3.pages["1"] = [[
    entry("201", "Cedar Workshop overview.md"),   # substring trap
    entry("202", "Cedar Works proposal.md"),      # alias only, case required
    entry("203", "CW-104 notes.md"),              # case only, alias required
    entry("204", "Cedar Works CW-104 SOW.md"),    # both with boundaries
]]
for fid in ("201", "202", "203", "204"):
    cli3.texts[fid] = (0, "generic text", True, False)

res3 = wf.gather_customer_files(cli3, "1",
                                [cust("Cedar Works", ["Cedar Works"], ["CW-104"])])
conf = sorted(f["file_id"] for f in res3["confirmed_files"])
amb = {f["file_id"]: f["ambiguity"] for f in res3["ambiguous_files"]}
check("f3: only the both-matching file confirmed", conf == ["204"], conf)
check("f3: Cedar Workshop is ambiguous, not confirmed",
      "201" in amb and any("boundary" in a["reason"] for a in amb["201"]), amb)
check("f3: alias-only file is ambiguous (case unsatisfied)",
      "202" in amb and any("case constraint not satisfied" in a["reason"]
                           for a in amb["202"]), amb)
check("f3: case-only file is ambiguous (alias unsatisfied)",
      "203" in amb and any("alias constraint not satisfied" in a["reason"]
                           for a in amb["203"]), amb)

# alias alternatives are OR
cli3b = FakeCli()
cli3b.pages["1"] = [[entry("301", "CW summary.md")]]
cli3b.texts["301"] = (0, "x", True, False)
res3b = wf.gather_customer_files(cli3b, "1",
                                 [cust("Cedar Works", ["Cedar Works", "CW"], [])])
check("f3b: alias alternatives are OR",
      [f["file_id"] for f in res3b["confirmed_files"]] == ["301"])

# ---------------- failure 4: max_files bound -> incomplete ----------------
c4 = FakeCli()
c4.pages["300"] = [[entry("c1", "Partner MSA - A.md"),
                    entry("c2", "Partner MSA - B.md")]]
c4.texts["c1"] = (0, "Agreement expires 2026-05-01.", True, False)
c4.texts["c2"] = (0, "Agreement expires 2026-06-01.", True, False)
res4 = wf.review_contracts(c4, "300", 2026, max_files=1)
check("f4: max_files bound -> coverage incomplete",
      res4["coverage"]["complete"] is False
      and any(g.get("reason") == "max_files bound reached"
              for g in res4["coverage"]["gaps"]), res4["coverage"])

# ---------------- failure 5: amendment supersedes base ----------------
c5 = FakeCli()
c5.pages["300"] = [[entry("b1", "Partner Agreement - Base.md"),
                    entry("b2", "Partner Agreement - Base Amendment 1.md")]]
c5.texts["b1"] = (0, "Partner agreement. Term expires 2027-06-30.", True, False)
c5.texts["b2"] = (0, "Amendment 1 to Partner Agreement - Base. "
                      "Extends expiration to 2028-01-15.", True, False)
res5 = wf.review_contracts(c5, "300", 2027)
exp_ids = [e["file_id"] for e in res5["expiring_in_year"]]
nr = {e["file_id"]: e for e in res5["needs_review"]}
check("f5: base not kept at stale 2027 expiration", "b1" not in exp_ids, exp_ids)
check("f5: base routed to needs_review with both sources",
      "b1" in nr and any(s["file_id"] == "b2"
                         for s in nr["b1"].get("amendment_sources", []))
      and "superseded" in nr["b1"]["reason"], nr.get("b1"))
check("f5: amendment kept in amendments bucket",
      [a["file_id"] for a in res5["amendments"]] == ["b2"]
      and res5["amendments"][0]["amends_file_id"] == "b1")

# ---------------- truncated extraction: no definitive conclusion ----------------
c6 = FakeCli()
c6.pages["300"] = [[entry("t1", "Partner MSA - Trunc.md")]]
c6.texts["t1"] = (0, "Agreement expires 2026-04-01. " + "x" * 500, True, True)
res6 = wf.review_contracts(c6, "300", 2026)
check("truncated extraction -> needs_review, not definitive",
      [e["file_id"] for e in res6["expiring_in_year"]] == []
      and any(e["file_id"] == "t1" and "truncated" in e["reason"]
              for e in res6["needs_review"]),
      [e["file_id"] for e in res6["needs_review"]])

# ---------------- invalid calendar date dropped ----------------
c7 = FakeCli()
c7.pages["300"] = [[entry("d1", "Partner MSA - BadDate.md")]]
c7.texts["d1"] = (0, "Agreement expires 2026-02-30.", True, False)
res7 = wf.review_contracts(c7, "300", 2026)
check("invalid calendar date is not a candidate",
      [e["file_id"] for e in res7["expiring_in_year"]] == []
      and any(e["file_id"] == "d1" for e in res7["needs_review"]))

# ---------------- cycle dedupe ----------------
c8 = FakeCli()
c8.pages["1"] = [[entry("10", "A", "folder")]]
c8.pages["10"] = [[entry("1", "back-to-root", "folder"),
                   entry("801", "doc.md")]]
c8.texts["801"] = (0, "x", True, False)
files8, cov8 = wf.traverse_folders(c8, "1")
check("cycle dedupe terminates",
      cov8["folders_scanned"] == 2 and len(files8) == 1, cov8)

# ---------------- generic filename via content evidence ----------------
c9 = FakeCli()
c9.pages["1"] = [[entry("901", "notes.md")]]
c9.texts["901"] = (0, "Meeting with Cedar Works about case CW-104.", True, False)
res9 = wf.gather_customer_files(c9, "1",
                                [cust("Cedar Works", ["Cedar Works"], ["CW-104"])],
                                max_content_reads=5)
check("generic filename confirmed via verified content",
      [f["file_id"] for f in res9["confirmed_files"]] == ["901"]
      and res9["coverage"]["complete"] is True, res9)

c9b = FakeCli()
c9b.pages["1"] = [[entry("902", "notes.md")]]
c9b.texts["902"] = (0, "Meeting with Cedar Works about case CW-104.", True, False)
res9b = wf.gather_customer_files(c9b, "1",
                                 [cust("Cedar Works", ["Cedar Works"], ["CW-104"])],
                                 max_content_reads=0)
check("exhausted content budget -> unassessed and incomplete",
      [f["file_id"] for f in res9b["unassessed_files"]] == ["902"]
      and res9b["coverage"]["complete"] is False, res9b["coverage"])

# unverified content never confirms
c9c = FakeCli()
c9c.pages["1"] = [[entry("903", "notes.md")]]
c9c.texts["903"] = (0, "Meeting with Cedar Works about case CW-104.", False, False)
res9c = wf.gather_customer_files(c9c, "1",
                                 [cust("Cedar Works", ["Cedar Works"], ["CW-104"])])
check("unverified content does not confirm",
      [f["file_id"] for f in res9c["confirmed_files"]] == [], res9c)

# folder context as evidence
c9d = FakeCli()
c9d.pages["1"] = [[entry("20", "Cedar Works", "folder")]]
c9d.pages["20"] = [[entry("904", "CW-104 summary.md")]]
c9d.texts["904"] = (0, "x", True, False)
res9d = wf.gather_customer_files(c9d, "1",
                                 [cust("Cedar Works", ["Cedar Works"], ["CW-104"])])
check("folder context plus name signals confirm",
      [f["file_id"] for f in res9d["confirmed_files"]] == ["904"], res9d)

# ---------------- cache isolation: per-customer pattern evaluation ----------------
for order_name, first in (("cedar-first", 0), ("other-first", 1)):
    ca = FakeCli()
    ca.pages["1"] = [[entry("n1", "notes.txt")]]
    ca.texts["n1"] = (0, "Customer: Cedar Works. Case: CW-104.", True, False)
    custs = [cust("Cedar Works", ["Cedar Works"], ["CW-104"]),
             cust("Other Company", ["Other Company"], ["OTHER-99"])]
    if first == 1:
        custs.reverse()
    resa = wf.gather_customer_files(ca, "1", custs, max_content_reads=5)
    conf_files = resa["confirmed_files"]
    check(f"cache isolation {order_name}: only Cedar Works confirmed",
          len(conf_files) == 1 and conf_files[0]["matched_customers"] == ["Cedar Works"],
          [(f["file_id"], f["matched_customers"]) for f in conf_files])
    check(f"cache isolation {order_name}: Other Company not confirmed",
          all("Other Company" not in f.get("matched_customers", [])
              for f in conf_files))

# ---------------- unresolved constraint triggers content read ----------------
cb = FakeCli()
cb.pages["1"] = [[entry("n2", "Cedar Works notes.txt")]]
cb.texts["n2"] = (0, "Customer: Cedar Works. Case: CW-104.", True, False)
resb = wf.gather_customer_files(cb, "1",
                                [cust("Cedar Works", ["Cedar Works"], ["CW-104"])],
                                max_content_reads=5)
check("unresolved case constraint reads content -> confirmed",
      [f["file_id"] for f in resb["confirmed_files"]] == ["n2"],
      [f["file_id"] for f in resb["ambiguous_files"]])

# truncated content never confirms, even with matching body
cc = FakeCli()
cc.pages["1"] = [[entry("n3", "Cedar Works notes.txt")]]
cc.texts["n3"] = (0, "Customer: Cedar Works. Case: CW-104.", True, True)
resc = wf.gather_customer_files(cc, "1",
                                [cust("Cedar Works", ["Cedar Works"], ["CW-104"])],
                                max_content_reads=5)
check("truncated content does not confirm",
      [f["file_id"] for f in resc["confirmed_files"]] == []
      and any(f["file_id"] == "n3" and
              any("truncated" in a["reason"] for a in f["ambiguity"])
              for f in resc["ambiguous_files"]),
      [f["file_id"] for f in resc["ambiguous_files"]])

# ---------------- input validation ----------------
ok, prob = wf._parse_customer_tokens([("alias", "x")])
check("alias before customer rejected", ok is None and "before any --customer" in prob)
ok, prob = wf._parse_customer_tokens([("customer", "Acme")])
check("customer without alias/case rejected", ok is None)
resv = wf.gather_customer_files(FakeCli(), "abc", [cust("A", ["A"], [])])
check("non-numeric folder rejected", resv["ok"] is False)
resv2 = wf.review_contracts(FakeCli(), "1", "20xx")
check("bad year rejected", resv2["ok"] is False)

print(f"ALL {PASS_COUNT} WORKFLOW TESTS PASSED")
