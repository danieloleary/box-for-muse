#!/usr/bin/env python3
"""Bounded enterprise workflows over the Box connector's existing operations.

Two read-only workflows:

  gather_customer_files: collect files for a customer case or meeting from an
      explicit folder scope, traversing descendants with global folder/page/
      file bounds and cycle dedupe. Customer alias alternatives are OR within
      aliases; when alias and case constraints are both supplied they must both
      match with word boundaries. Ambiguous candidates are reported separately,
      never confirmed. Generic filenames are assessed with bounded, verified
      content evidence plus folder context, not filename-only matching.

  review_contracts: identify partner contracts expiring in a calendar year via
      two-pass relation analysis. Every finding carries source file ID, file
      version, sha1, and clause snippets. A possible applicable amendment routes
      the base agreement to needs_review with both sources cited; a stale
      definitive expiration is never kept. Partial/truncated extraction never
      produces definitive portfolio conclusions. Dates are validated with
      calendar parsing.

Regex finds candidate dates and clause snippets; it never establishes legal
interpretation. When extraction cannot resolve terms reliably, the workflow
returns evidence for agent review instead of a conclusion.

No writes, no uploads, no policy changes. All network goes through the
injected `cli` module (the installed bin/box), so tests substitute fakes.
"""

from __future__ import annotations

import datetime
import importlib.machinery
import importlib.util
import io
import json
import re
import sys
from types import SimpleNamespace
from urllib.parse import urlencode

DEFAULT_MAX_FOLDERS = 25
DEFAULT_MAX_PAGES = 50
DEFAULT_MAX_FILES = 500
DEFAULT_MAX_CONTENT_READS = 25
EVIDENCE_PER_FILE_BYTES = 8000
EVIDENCE_TOTAL_BYTES = 32000


def load_cli(path: str):
    """Load the installed bin/box as a module without executing main()."""
    loader = importlib.machinery.SourceFileLoader("boxcli_workflow", path)
    spec = importlib.util.spec_from_loader("boxcli_workflow", loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _err(hint: str) -> dict:
    return {"ok": False, "hint": hint}


def _validate_folder(cli, folder_id: str):
    if not cli.valid_id(folder_id or ""):
        return _err("folder_id must be an explicit numeric Box folder ID")
    return None


def _validate_year(year):
    try:
        y = int(year)
    except (TypeError, ValueError):
        return None, _err("year must be a four-digit calendar year")
    if not 1900 <= y <= 2100:
        return None, _err("year must be between 1900 and 2100")
    return y, None


# ---------------------------------------------------------------- traversal

def traverse_folders(cli, root_folder_id: str,
                     max_folders=DEFAULT_MAX_FOLDERS,
                     max_pages=DEFAULT_MAX_PAGES,
                     max_files=DEFAULT_MAX_FILES,
                     page_limit=100):
    """BFS traversal of a folder tree. Returns (files, coverage).

    files: [{"entry", "folder_id", "folder_path"}] with folder_path a list of
    ancestor folder names from the root. Deduplicated by file ID; folders
    deduplicated by folder ID (cycle safe).

    coverage.complete is False whenever any folder was inaccessible, skipped,
    or a bound was reached; gaps describe each one.
    """
    coverage = {"ok": True, "complete": True, "gaps": [],
                "folders_scanned": 0, "pages_scanned": 0, "files_found": 0}
    problem = _validate_folder(cli, root_folder_id)
    if problem:
        coverage["ok"] = False
        coverage["complete"] = False
        coverage["gaps"].append({"reason": "invalid folder", "hint": problem["hint"]})
        return [], coverage

    files, seen_files = [], set()
    visited = set()
    queue = [(root_folder_id, ["folder:" + root_folder_id])]
    page_budget = max_pages
    bounded = False

    while queue and not bounded:
        if len(visited) >= max_folders:
            coverage["complete"] = False
            coverage["gaps"].append({"reason": "max_folders bound reached",
                                    "folders_scanned": len(visited)})
            break
        fid, path = queue.pop(0)
        if fid in visited:
            continue
        visited.add(fid)
        offset = 0
        while True:
            if page_budget <= 0:
                coverage["complete"] = False
                coverage["gaps"].append({"reason": "max_pages bound reached",
                                        "folder_id": fid, "folder_path": path})
                bounded = True
                break
            params = {"limit": str(page_limit), "offset": str(offset),
                      "fields": "id,type,name,size,sha1,file_version"}
            url = f"{cli.API_BASE}/folders/{fid}/items?" + urlencode(params)
            status, body, _ = cli.do_request(url)
            page_budget -= 1
            coverage["pages_scanned"] += 1
            if status != 200:
                coverage["complete"] = False
                coverage["gaps"].append({"folder_id": fid, "folder_path": path,
                                        "status": status,
                                        "reason": "inaccessible folder"})
                break
            try:
                page = json.loads(body.decode("utf-8"))
            except Exception:
                coverage["complete"] = False
                coverage["gaps"].append({"folder_id": fid, "folder_path": path,
                                        "reason": "page body not parseable"})
                break
            if not isinstance(page, dict):
                page = {}
            total = page.get("total_count")
            response_offset = page.get("offset", offset)
            response_limit = page.get("limit", page_limit)
            entries = page.get("entries")
            if (type(total) is not int or total < 0 or
                    type(response_offset) is not int or response_offset != offset or
                    type(response_limit) is not int or response_limit <= 0 or
                    not isinstance(entries, list) or
                    any(not isinstance(e, dict) for e in entries)):
                coverage["complete"] = False
                coverage["gaps"].append({"folder_id": fid,
                                        "reason": "invalid pagination response"})
                break
            for e in entries:
                eid = e.get("id")
                if not eid:
                    continue
                if e.get("type") == "folder":
                    queue.append((eid, path + [e.get("name") or eid]))
                elif e.get("type") == "file" and eid not in seen_files:
                    seen_files.add(eid)
                    files.append({"entry": e, "folder_id": fid,
                                  "folder_path": path})
                    coverage["files_found"] += 1
                    if len(files) >= max_files:
                        coverage["complete"] = False
                        coverage["gaps"].append(
                            {"reason": "max_files bound reached",
                             "files_found": coverage["files_found"]})
                        bounded = True
                        break
            if bounded:
                break
            offset += response_limit
            if offset >= total:
                break
            if offset > 9999:
                coverage["complete"] = False
                coverage["gaps"].append({"folder_id": fid,
                                        "reason": "offset limit reached"})
                break
        coverage["folders_scanned"] += 1
    return files, coverage


# ---------------------------------------------------------------- matching

def _boundary_res(values):
    return [re.compile(r"\b" + re.escape(v) + r"\b", re.IGNORECASE)
            for v in values if v]


def _match_any(patterns, text):
    return any(p.search(text or "") for p in patterns)


def _substr_any(values, text):
    t = (text or "").lower()
    return any(v.lower() in t for v in values if v)


def _parse_customer_tokens(tokens):
    """tokens: ordered (kind, value) with kind in customer|alias|case."""
    customers = []
    current = None
    for kind, value in tokens or []:
        value = (value or "").strip()
        if kind == "customer":
            if not value:
                return None, "customer name must not be empty"
            current = {"name": value, "aliases": [], "cases": []}
            customers.append(current)
        elif kind in ("alias", "case"):
            if current is None:
                return None, f"{kind} {value!r} appears before any --customer"
            if not value:
                return None, f"{kind} value must not be empty"
            current["aliases" if kind == "alias" else "cases"].append(value)
        else:
            return None, f"unknown token kind {kind!r}"
    if not customers:
        return None, "at least one --customer is required"
    for c in customers:
        if not c["aliases"] and not c["cases"]:
            return None, f"customer {c['name']!r} needs at least one --alias or --case"
    return customers, None


def _read_text_via_cli(cli, file_id: str):
    """Reuse the installed read-file path (integrity gate included)."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = cli.cmd_read_file(SimpleNamespace(file_id=file_id, out=None, text=True))
    finally:
        sys.stdout = old
    try:
        data = json.loads(buf.getvalue())
    except Exception:
        return rc, None
    return rc, data


def _assess_file(cli, f, customer, content_cache, content_budget):
    """Return (status, detail) for one file against one customer.

    status: confirmed | ambiguous | unmatched | unassessed. Content is read
    (bounded) whenever a required constraint remains unresolved after name
    and folder signals. The cache stores verified text and read metadata by
    file ID; each customer's patterns are evaluated separately against the
    cached text. Unverified or truncated content never confirms.
    """
    entry = f["entry"]
    name = entry.get("name") or ""
    folder_text = " / ".join(f["folder_path"])
    alias_res = _boundary_res(customer["aliases"])
    case_res = _boundary_res(customer["cases"])
    has_alias = bool(customer["aliases"])
    has_case = bool(customer["cases"])

    alias_ok = _match_any(alias_res, name) or _match_any(alias_res, folder_text)
    case_ok = _match_any(case_res, name) or _match_any(case_res, folder_text)

    content_note = None
    if (has_alias and not alias_ok) or (has_case and not case_ok):
        fid = entry.get("id")
        if fid in content_cache:
            content_text, content_note, version, extraction = content_cache[fid]
        elif content_budget["remaining"] > 0:
            content_budget["remaining"] -= 1
            rc, data = _read_text_via_cli(cli, fid)
            version = (data or {}).get("version", {}) if data else {}
            extraction = (data or {}).get("extraction", {}) if data else {}
            content_text, content_note = None, "content unreadable or unverified"
            if (rc == 0 and data and data.get("ok") and version.get("verified")
                    and version.get("file_version_id") and version.get("sha1")
                    and data.get("version_changed_during_read", False) is False
                    and ("version_after" not in data or data.get("version_after"))
                    and not data.get("version_check_note")):
                content_text = extraction.get("text", "")
                if extraction.get("truncated") or extraction.get("status") != "ok":
                    # partial extraction is evidence only; never confirms
                    content_note = "content extraction partial or truncated; evidence partial"
                else:
                    content_note = None
            version = dict(version)
            if data:
                for key in ("version_changed_during_read", "version_check_note", "version_after"):
                    if key in data:
                        version[key] = data[key]
            content_cache[fid] = (content_text, content_note, version, extraction)
        else:
            content_budget["exhausted"] = True
            return ("unassessed",
                    "content-read bound reached; required constraint unresolved")
        if (content_text is not None
                and content_note != "content extraction partial or truncated; evidence partial"):
            if has_alias and not alias_ok:
                alias_ok = _match_any(alias_res, content_text)
            if has_case and not case_ok:
                case_ok = _match_any(case_res, content_text)
    if content_note == "content unreadable or unverified":
        return "unassessed", content_note
    partial = (content_note == "content extraction partial or truncated; evidence partial")

    if has_alias and has_case:
        if alias_ok and case_ok:
            return "confirmed", "alias and case both matched with boundaries"
        reasons = []
        if _substr_any(customer["aliases"], name) and not alias_ok:
            reasons.append("alias substring without word boundary")
        if _substr_any(customer["cases"], name) and not case_ok:
            reasons.append("case substring without word boundary")
        if alias_ok and not case_ok:
            reasons.append("alias matched but case constraint not satisfied")
        if case_ok and not alias_ok:
            reasons.append("case matched but alias constraint not satisfied")
        if partial:
            reasons.append("content extraction partial or truncated; evidence partial")
        return "ambiguous", "; ".join(reasons) or "no boundary match"
    if has_alias:
        if alias_ok:
            return "confirmed", "alias matched with boundaries"
        if partial:
            return "ambiguous", "content extraction partial or truncated; evidence partial"
        if _substr_any(customer["aliases"], name):
            return "ambiguous", "alias substring without word boundary"
        return "unmatched", "no alias match"
    if case_ok:
        return "confirmed", "case matched with boundaries"
    if partial:
        return "ambiguous", "content extraction partial or truncated; evidence partial"
    if _substr_any(customer["cases"], name):
        return "ambiguous", "case substring without word boundary"
    return "unmatched", "no case match"


def _cached_evidence(cached, remaining):
    """Expose only already-read verified evidence, bounded in UTF-8 bytes."""
    if not cached or cached[0] is None:
        return {"available": False, "complete": False,
                "reason": cached[1] if cached else "content not read by gather"}, 0
    text, note, version, extraction = cached
    raw = text.encode("utf-8")
    shown = raw[:min(EVIDENCE_PER_FILE_BYTES, remaining)].decode("utf-8", errors="ignore")
    used = len(shown.encode("utf-8"))
    capped = used < len(raw)
    metadata = {key: extraction.get(key) for key in
                ("status", "format", "total_length", "truncated", "hint", "limits")}
    complete = not capped and not extraction.get("truncated") and extraction.get("status") == "ok"
    return {"available": True, "complete": complete, "text": shown,
            "text_bytes": used, "cached_text_bytes": len(raw),
            "output_truncated": capped, "extraction": metadata,
            "source": dict(version), "note": note}, used


def gather_customer_files(cli, folder_id: str, customers,
                          max_folders=DEFAULT_MAX_FOLDERS,
                          max_pages=DEFAULT_MAX_PAGES,
                          max_files=DEFAULT_MAX_FILES,
                          max_content_reads=DEFAULT_MAX_CONTENT_READS,
                          include_evidence=False):
    """Collect customer files across a folder tree.

    Confirmed files matched alias (OR within aliases) and, when both are
    supplied, case constraints, with word boundaries. Ambiguous candidates are
    listed separately, never confirmed.
    """
    files, coverage = traverse_folders(cli, folder_id, max_folders,
                                       max_pages, max_files)
    if not coverage.get("ok"):
        return {"ok": False, "hint": coverage["gaps"][0].get("hint", "invalid folder"),
                "coverage": coverage}
    confirmed, ambiguous, unmatched, unassessed = [], [], [], []
    per_customer = {c["name"]: 0 for c in customers}
    content_cache, content_budget = {}, {"remaining": max_content_reads,
                                        "exhausted": False}
    evidence_remaining = EVIDENCE_TOTAL_BYTES
    evidence_complete = True
    files_without_evidence = 0
    for f in files:
        entry = f["entry"]
        fv = entry.get("file_version") or {}
        record = {"file_id": entry.get("id"), "name": entry.get("name"),
                  "folder_path": f["folder_path"],
                  "source": {"file_version_id": fv.get("id"),
                             "sha1": entry.get("sha1"),
                             "size": entry.get("size")}}
        file_status = "unmatched"
        amb_reasons, unassess_reason = [], None
        matched_customers = []
        for customer in customers:
            status, reason = _assess_file(cli, f, customer, content_cache,
                                         content_budget)
            if status in ("unassessed", "ambiguous") and (
                    "content" in reason or "unverified" in reason):
                coverage["complete"] = False
                coverage["gaps"].append({"file_id": entry.get("id"),
                                        "customer": customer["name"], "reason": reason})
            if status == "confirmed":
                file_status = "confirmed"
                matched_customers.append(customer["name"])
                per_customer[customer["name"]] += 1
            elif status == "ambiguous" and file_status != "confirmed":
                file_status = "ambiguous"
                amb_reasons.append({"customer": customer["name"],
                                    "reason": reason})
            elif status == "unassessed" and file_status == "unmatched":
                file_status = "unassessed"
                unassess_reason = reason
        cached = content_cache.get(entry.get("id"))
        if cached and cached[2].get("verified"):
            record["listing_source"] = record["source"]
            record["source"] = dict(cached[2])
        record["source_url"] = "https://app.box.com/file/" + str(entry.get("id"))
        record["match_kind"] = "identifier evidence; not proof of relevance or approval"
        record["matched_customers"] = matched_customers
        if include_evidence:
            evidence, used = _cached_evidence(cached, evidence_remaining)
            evidence_remaining -= used
            record["evidence"] = evidence
            evidence_complete = evidence_complete and evidence["complete"]
            files_without_evidence += int(not evidence["available"])
            if evidence.get("output_truncated"):
                coverage["complete"] = False
                coverage["gaps"].append({"file_id": entry.get("id"),
                                        "reason": "returned evidence byte cap reached; text incomplete"})
        if file_status == "confirmed":
            confirmed.append(record)
        elif file_status == "ambiguous":
            record["ambiguity"] = amb_reasons
            ambiguous.append(record)
        elif file_status == "unassessed":
            record["reason"] = unassess_reason
            unassessed.append(record)
        else:
            unmatched.append(record)
    if content_budget["exhausted"]:
        coverage["complete"] = False
        coverage["gaps"].append({"reason": "content-read bound reached",
                                "unassessed_files": len(unassessed)})
    result = {"ok": True, "folder_id": folder_id,
            "customers": [{"name": c["name"], "aliases": c["aliases"],
                           "cases": c["cases"]} for c in customers],
            "files_scanned": len(files),
            "confirmed_files": confirmed,
            "ambiguous_files": ambiguous,
            "unmatched_files": unmatched,
            "unassessed_files": unassessed,
            "per_customer_counts": per_customer,
            "coverage": coverage}
    if include_evidence:
        result["evidence_summary"] = {
            "complete": evidence_complete, "files_without_evidence": files_without_evidence,
            "text_bytes": EVIDENCE_TOTAL_BYTES - evidence_remaining,
            "per_file_byte_limit": EVIDENCE_PER_FILE_BYTES,
            "total_byte_limit": EVIDENCE_TOTAL_BYTES,
            "scope": "cached reads only; no additional downloads"}
    return result


# ---------------------------------------------------------------- contracts

MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

DATE_RES = [
    re.compile(r"\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b"),
    re.compile(r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(19|20)\d{2}\b"),
    re.compile(r"\b(January|February|March|April|May|June|July|August|September|"
               r"October|November|December)\s+(\d{1,2}),\s+((19|20)\d{2})\b",
               re.IGNORECASE),
]

EXPIRY_RES = [re.compile(p, re.IGNORECASE) for p in
              [r"expir\w*", r"termination date", r"\bend date\b",
               r"effective through", r"valid through", r"\bexpires\b",
               r"term ends?", r"contract end"]]
RENEW_RES = [re.compile(p, re.IGNORECASE) for p in
             [r"auto-?\s?renew", r"automatically renew", r"\bevergreen\b",
              r"renewal term", r"\brenewal\b"]]
NEG_RENEW_RES = [re.compile(p, re.IGNORECASE) for p in
                 [r"does not auto-?renew", r"will not renew",
                  r"no auto-?renew", r"shall not renew"]]
NOTICE_RES = [re.compile(p, re.IGNORECASE) for p in
              [r"notice period", r"\bnotice\b.{0,20}\bday", r"terminate.{0,40}notice",
               r"notice of (non-?renewal|termination)", r"\bnotice\s+(due|deadline|by)\b"]]

CONTRACT_NAME_RE = re.compile(
    r"contract|agreement|\bmsa\b|\bsow\b|amendment|terms|order form", re.IGNORECASE)


def _valid_ymd(y, m, d):
    try:
        datetime.date(y, m, d)
        return True
    except ValueError:
        return False


def _all_dates(text: str):
    """Calendar-validated dates; invalid calendar dates are dropped."""
    found = []
    for rx in DATE_RES:
        for m in rx.finditer(text or ""):
            try:
                if rx is DATE_RES[0]:
                    d = (int(m.group(0)[:4]), int(m.group(0)[5:7]),
                         int(m.group(0)[8:10]))
                elif rx is DATE_RES[1]:
                    a, b, c = m.group(0).split("/")
                    d = (int(c), int(a), int(b))
                else:
                    month = MONTHS[m.group(1).lower()]
                    d = (int(m.group(3)), month, int(m.group(2)))
                if d not in found and _valid_ymd(*d):
                    found.append(d)
            except (ValueError, KeyError):
                continue
    return found


def _window_snippets(text: str, patterns, width=140):
    # Keep dates within their clause. Broad character windows can attach the
    # next sentence's notice deadline to an expiration phrase.
    snippets = []
    for clause in re.split(r"[.;\n]+", text or ""):
        if any(rx.search(clause) for rx in patterns):
            snippet = " ".join(clause.split())
            if snippet and snippet not in snippets:
                snippets.append(snippet)
    return snippets


def _distinct_dates(snippets):
    dates = set()
    for s in snippets:
        for d in _all_dates(s):
            dates.add(d)
    return sorted(dates)


def extract_contract_signals(text: str) -> dict:
    """Regex evidence only. Never legal interpretation."""
    expiry_snips = _window_snippets(text, EXPIRY_RES)
    renew_snips = _window_snippets(text, RENEW_RES)
    notice_snips = _window_snippets(text, NOTICE_RES)
    exp_dates = _distinct_dates(expiry_snips)
    notice_dates = _distinct_dates(notice_snips)
    negated = any(rx.search(text or "") for rx in NEG_RENEW_RES)
    evergreen = bool(re.search(r"\bevergreen\b", text or "", re.IGNORECASE))
    auto_renew = (bool(renew_snips) or evergreen) and not negated
    return {
        "expiry_snippets": expiry_snips[:5],
        "renewal_snippets": renew_snips[:5],
        "notice_snippets": notice_snips[:5],
        "candidate_expiration_dates": ["%04d-%02d-%02d" % d for d in exp_dates],
        "candidate_notice_dates": ["%04d-%02d-%02d" % d for d in notice_dates],
        "auto_renewal_indicated": auto_renew,
        "evergreen_indicated": evergreen,
        "renewal_negated": negated,
    }


def _cite(entry: dict, version: dict | None = None) -> dict:
    fv = entry.get("file_version") or {}
    cite = {"file_id": entry.get("id"), "name": entry.get("name"),
            "source_url": "https://app.box.com/file/" + str(entry.get("id")),
            "file_version_id": (version or {}).get("file_version_id") or fv.get("id"),
            "sha1": (version or {}).get("sha1") or entry.get("sha1"),
            "verified": (version or {}).get("verified")}
    return cite


def _norm_name(name: str) -> str:
    n = (name or "").lower()
    n = re.sub(r"\.[a-z0-9]+$", "", n)
    return re.sub(r"\s+", " ", n).strip(" -_.")


def _amendment_base_key(name: str) -> str:
    n = _norm_name(name)
    return re.sub(r"\s*amendment\s*\d*\s*", " ", n).strip(" -_.")


def review_contracts(cli, folder_id: str, year,
                     max_files=DEFAULT_MAX_FILES,
                     max_folders=DEFAULT_MAX_FOLDERS,
                     max_pages=DEFAULT_MAX_PAGES):
    """Two-pass contract review with relation analysis.

    Pass 1: traverse, read candidate files (bounded), extract signals.
    Pass 2: resolve relations. A base agreement with a possible applicable
    amendment goes to needs_review citing both sources; a stale definitive
    expiration is never kept. Truncated extraction never yields a definitive
    portfolio conclusion.
    """
    target_year, problem = _validate_year(year)
    if problem:
        return problem
    files, coverage = traverse_folders(cli, folder_id, max_folders,
                                       max_pages, max_files)
    if not coverage.get("ok"):
        return {"ok": False, "hint": coverage["gaps"][0].get("hint", "invalid folder"),
                "coverage": coverage}

    out = {"ok": True, "folder_id": folder_id, "year": target_year,
           "bounded_by": {"max_files": max_files},
           "files_scanned": 0,
           "expiring_in_year": [], "evergreen": [], "outside_year": [],
           "needs_review": [], "drafts": [], "amendments": [],
           "skipped_non_contract": [], "unreadable": [],
           "coverage": coverage}

    # ---- pass 1: provisional classification
    provisional = []
    name_index = {}
    for f in files:
        name_index.setdefault(_norm_name(f["entry"].get("name")), f["entry"].get("id"))
    scanned = 0
    for f in files:
        entry = f["entry"]
        name = entry.get("name") or ""
        if scanned >= max_files:
            break
        scanned += 1
        rc, data = _read_text_via_cli(cli, entry["id"])
        if rc != 0 or not data or not data.get("ok"):
            out["unreadable"].append({**_cite(entry),
                                      "reason": "could not read or verify file text"})
            continue
        version = data.get("version", {})
        if (not version.get("verified") or not version.get("file_version_id")
                or not version.get("sha1") or data.get("version_changed_during_read")
                or data.get("version_check_note")):
            out["unreadable"].append({**_cite(entry, version),
                                      "reason": "file bytes not verified"})
            continue
        text = (data.get("extraction") or {}).get("text", "")
        extraction = data.get("extraction") or {}
        truncated = bool(extraction.get("truncated") or extraction.get("status") != "ok")
        lname = name.lower()
        is_amendment = "amendment" in lname
        is_draft = ("draft" in lname or
                    bool(re.search(r"document status:\s*draft", text, re.IGNORECASE)))
        signals = extract_contract_signals(text)
        cite = {**_cite(entry, version), "folder_path": f["folder_path"]}
        if truncated:
            cite["evidence_note"] = "text extraction incomplete; signals from available text only"
        provisional.append({"cite": cite, "signals": signals,
                            "is_amendment": is_amendment, "is_draft": is_draft,
                            "truncated": truncated, "name": name})
    out["files_scanned"] = scanned

    enumeration_complete = coverage["complete"]
    # link amendments to base files
    for p in provisional:
        p["amends_file_id"] = None
        if p["is_amendment"]:
            key = _amendment_base_key(p["name"])
            for q in provisional:
                if q["cite"]["file_id"] == p["cite"]["file_id"]:
                    continue
                qn = _norm_name(q["name"])
                if key and (key in qn or qn in key):
                    p["amends_file_id"] = q["cite"]["file_id"]
                    break

    # ---- pass 2: relation resolution and bucketing
    for p in provisional:
        cite, signals = p["cite"], p["signals"]
        entry = {**cite, "signals": signals}
        if p["is_amendment"]:
            entry["amends_file_id"] = p["amends_file_id"]
            if p["is_draft"]:
                entry["note"] = "draft amendment; not applied"
            out["amendments"].append(entry)
            continue
        if p["is_draft"]:
            out["drafts"].append({**entry, "reason": "draft; not authoritative"})
            continue
        applicable = [a for a in provisional
                      if a["is_amendment"] and not a["is_draft"]
                      and a["amends_file_id"] == cite["file_id"]]
        if applicable:
            out["needs_review"].append({
                **entry,
                "reason": ("possible applicable amendment; base expiration may be "
                           "superseded"),
                "amendment_sources": [
                    {"file_id": a["cite"]["file_id"], "name": a["name"],
                     "file_version_id": a["cite"]["file_version_id"],
                     "candidate_expiration_dates":
                         a["signals"]["candidate_expiration_dates"]}
                    for a in applicable]})
            continue
        draft_amends = [a["cite"]["file_id"] for a in provisional
                        if a["is_amendment"] and a["is_draft"]
                        and a["amends_file_id"] == cite["file_id"]]
        if draft_amends:
            entry["note"] = ("draft amendment exists but is not applied: "
                             + ", ".join(draft_amends))
        if p["truncated"]:
            out["needs_review"].append({
                **entry,
                "reason": "extraction partial or truncated; date evidence incomplete"})
            continue
        exp_dates = signals["candidate_expiration_dates"]
        if len(exp_dates) > 1:
            out["needs_review"].append({
                **entry,
                "reason": "multiple candidate expiration dates; ambiguous"})
        elif signals["evergreen_indicated"] and not exp_dates:
            out["evergreen"].append(entry)
        elif len(exp_dates) == 1:
            entry["expiration_date"] = exp_dates[0]
            entry["notice_dates"] = signals["candidate_notice_dates"]
            if int(exp_dates[0][:4]) == target_year:
                out["expiring_in_year"].append(entry)
            else:
                out["outside_year"].append(entry)
        else:
            out["needs_review"].append({**entry,
                                        "reason": "no expiration date found"})
    # These are discovery hints, never a legal or portfolio conclusion.
    out["evidence_only"] = True
    out["assessment_complete"] = False
    out["candidate_expirations"] = out["expiring_in_year"]
    out["candidate_outside_year"] = out["outside_year"]
    out["expiring_in_year"] = []
    out["outside_year"] = []
    for item in out["candidate_expirations"] + out["candidate_outside_year"] + out["evergreen"]:
        item["requires_review"] = True
        out["needs_review"].append({**item, "reason":
            "candidate language only; verify current agreement, amendments, renewal and notice terms"})
    for key in ("needs_review", "amendments", "drafts", "unreadable"):
        for item in out[key]:
            item["requires_review"] = True
    if out["unreadable"]:
        coverage["complete"] = False
        coverage["gaps"].extend({"file_id": x["file_id"], "reason": x["reason"]}
                                for x in out["unreadable"])
    out["enumeration_complete"] = enumeration_complete
    out["unclassified_files"] = [x for x in out["needs_review"]
                                  if x.get("reason") == "no expiration date found"]
    if out["unclassified_files"] or any(p["truncated"] for p in provisional):
        coverage["complete"] = False
        coverage["gaps"].append({"reason": "partial extraction or unclassified contract evidence"})
    out["limitation"] = ("Every scoped file was considered within the stated bounds. "
                         "Date grammar and amendment matching are incomplete heuristics. "
                         "No result establishes all contracts or a definitive expiration.")
    return out
