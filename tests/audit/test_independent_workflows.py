"""Independent semantic acceptance tests. No production changes or Box access.

Run: python3 tests/audit/test_independent_workflows.py
BOX_WORKFLOW_SOURCE may point at a candidate workflows.py for revalidation.
"""
import importlib.util
import importlib.machinery
import contextlib
import io
import json
import os
from pathlib import Path
import socket
import sys
from types import SimpleNamespace
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('BOX_WORKFLOW_SOURCE', ROOT / 'src/box/workflows.py'))
spec = importlib.util.spec_from_file_location('independent_workflow', SOURCE)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

def deny_network(*args, **kwargs):
    raise AssertionError('Independent suite prohibits network access')
socket.socket.connect = deny_network
socket.create_connection = deny_network

def file(fid, name):
    return {'id': fid, 'type': 'file', 'name': name, 'size': 10,
            'sha1': 'listed-sha', 'file_version': {'id': 'listed-version'}}

def read(text, status='ok', version='read-version'):
    return {'ok': True, 'version': {'verified': True, 'file_version_id': version, 'sha1': 'read-sha'},
            'extraction': {'text': text, 'status': status, 'truncated': False}}

class Fake:
    API_BASE = 'https://api.box.com/2.0'
    valid_id = staticmethod(lambda v: str(v).isdigit())
    def __init__(self, entries, reads):
        self.entries, self.reads, self.read_ids = entries, reads, []
    def do_request(self, url):
        return 200, json.dumps({'entries': self.entries, 'offset': 0, 'limit': 100,
                                'total_count': len(self.entries)}).encode(), {}
    def cmd_read_file(self, args):
        self.read_ids.append(args.file_id)
        data = self.reads[args.file_id]
        print(json.dumps(data))
        return 0 if data.get('ok') else 1

CUSTOMERS = [{'name': 'Cedar Works', 'aliases': ['Cedar Works'], 'cases': []}]

class IndependentWorkflowAcceptance(unittest.TestCase):
    def test_unreadable_customer_candidate_is_not_a_negative_match(self):
        c = Fake([file('7', 'notes.txt')], {'7': {'ok': False, 'status': 403}})
        r = w.gather_customer_files(c, '9', CUSTOMERS)
        self.assertEqual(r['unmatched_files'], [], 'An unread file cannot establish absence of customer evidence')
        self.assertEqual(len(r['unassessed_files']), 1)
        self.assertFalse(r['coverage']['complete'])

    def test_verified_content_match_cites_actual_read_version(self):
        c = Fake([file('7', 'notes.txt')], {'7': read('Customer Cedar Works')})
        r = w.gather_customer_files(c, '9', CUSTOMERS)
        source = r['confirmed_files'][0]['source']
        self.assertEqual(source['file_version_id'], 'read-version')
        self.assertEqual(source['sha1'], 'read-sha')

    def test_unreadable_possible_amendment_prevents_definitive_base_expiry(self):
        c = Fake([file('7', 'Cedar agreement.txt'), file('8', 'Cedar agreement amendment 1.txt')],
                 {'7': read('This agreement expires December 31, 2027.'),
                  '8': {'ok': False, 'status': 403}})
        r = w.review_contracts(c, '9', 2027)
        self.assertEqual(r['expiring_in_year'], [], 'Unread amendment may supersede the base')
        self.assertTrue(any(x['file_id'] == '7' for x in r['needs_review']))

    def test_generic_filename_contract_is_not_asserted_noncontract(self):
        c = Fake([file('7', 'PartnerCo signed final.pdf')],
                 {'7': read('Partner agreement. This contract expires December 31, 2027.')})
        r = w.review_contracts(c, '9', 2027)
        if '7' in c.read_ids:
            candidates = r.get('candidate_expirations', []) + r.get('needs_review', [])
            self.assertTrue(any(x['file_id'] == '7' for x in candidates))
            self.assertTrue(r.get('evidence_only'), 'Candidate output must make its limit machine-readable')
        else:
            self.assertFalse(r['coverage']['complete'], 'Filename-only exclusion is a scope gap, not full portfolio coverage')

    def test_amendment_body_reference_is_not_ignored_when_filename_differs(self):
        c = Fake([file('7', 'Cedar agreement.txt'), file('8', 'Extension amendment.txt')],
                 {'7': read('Cedar agreement expires December 31, 2027.'),
                  '8': read('This amendment modifies Cedar agreement. The contract expires December 31, 2028.')})
        r = w.review_contracts(c, '9', 2027)
        self.assertEqual(r['expiring_in_year'], [], 'Unresolved amendment relation must not permit definite portfolio conclusion')

    def test_historical_expiry_does_not_become_current_expiry(self):
        c = Fake([file('7', 'Cedar agreement.txt')],
                 {'7': read('The prior agreement expired December 31, 2027. This replacement remains in force for three years from execution.')})
        r = w.review_contracts(c, '9', 2027)
        self.assertEqual(r['expiring_in_year'], [], 'Regex evidence cannot establish whether an expiry is operative')

    def test_unreadable_contract_marks_coverage_incomplete(self):
        c = Fake([file('7', 'Cedar agreement.txt')], {'7': {'ok': False, 'status': 403}})
        r = w.review_contracts(c, '9', 2027)
        self.assertFalse(r['coverage']['complete'])

    def test_partial_customer_text_is_ambiguous_not_confirmed(self):
        c = Fake([file('7', 'notes.docx')], {'7': read('Cedar Works', status='partial')})
        r = w.gather_customer_files(c, '9', CUSTOMERS)
        self.assertEqual(r['confirmed_files'], [])
        self.assertEqual(len(r['ambiguous_files']), 1)

    def test_filename_evidence_does_not_claim_content_verification(self):
        c = Fake([file('7', 'Cedar Works notes.txt')], {})
        r = w.gather_customer_files(c, '9', CUSTOMERS)
        self.assertEqual(c.read_ids, [])
        self.assertFalse(r['confirmed_files'][0]['source'].get('verified', False))

    def test_content_read_retains_unavailable_latest_version_note(self):
        data = read('Customer Cedar Works')
        data['version_check_note'] = 'post-download metadata fetch failed; version-change detection unavailable'
        data['version_after'] = None
        c = Fake([file('7', 'notes.txt')], {'7': data})
        r = w.gather_customer_files(c, '9', CUSTOMERS)
        self.assertIn('version-change detection unavailable', json.dumps(r),
                      'A verified old version must not silently imply current content')

    def test_content_read_missing_source_identifiers_is_unassessed(self):
        data = read('Customer Cedar Works')
        data['version'] = {'verified': True}
        c = Fake([file('7', 'notes.txt')], {'7': data})
        r = w.gather_customer_files(c, '9', CUSTOMERS)
        self.assertEqual(r['confirmed_files'], [], 'Missing source version/hash cannot yield a cited content match')
        self.assertFalse(r['coverage']['complete'])

    def test_contract_candidates_explicitly_require_review(self):
        c = Fake([file('7', 'Cedar agreement.txt')],
                 {'7': read('This contract expires December 31, 2027.')})
        r = w.review_contracts(c, '9', 2027)
        self.assertTrue(r.get('evidence_only'))
        self.assertEqual(r.get('expiring_in_year', []), [])
        candidates = r.get('candidate_expirations', [])
        self.assertEqual(len(candidates), 1)
        self.assertTrue(candidates[0].get('requires_review'))
        self.assertTrue(any(x['file_id'] == '7' for x in r['needs_review']))

    def test_contract_enumeration_is_separate_from_failed_assessment(self):
        c = Fake([file('7', 'Cedar agreement.txt')], {'7': {'ok': False, 'status': 403}})
        r = w.review_contracts(c, '9', 2027)
        self.assertTrue(r.get('enumeration_complete'), 'Folder listing succeeded even though content read failed')
        self.assertFalse(r['coverage']['complete'])
        self.assertFalse(r['assessment_complete'])

    def test_partial_contract_read_marks_content_coverage_incomplete(self):
        c = Fake([file('7', 'Cedar agreement.docx')],
                 {'7': read('This contract expires December 31, 2027.', status='partial')})
        r = w.review_contracts(c, '9', 2027)
        self.assertFalse(r['coverage']['complete'])
        self.assertTrue(r.get('enumeration_complete'))

    def test_draft_only_contract_cli_still_requires_review(self):
        cli_path = SOURCE.parent / 'bin/boxwork'
        loader = importlib.machinery.SourceFileLoader('independent_boxwork', str(cli_path))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        bw = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'workflows': w}):
            loader.exec_module(bw)
        c = Fake([file('7', 'Cedar draft agreement.txt')],
                 {'7': read('This contract expires December 31, 2027.')})
        args = SimpleNamespace(folder_id='9', year=2027, max_files=500, max_folders=25, max_pages=50)
        with patch.object(w, 'load_cli', return_value=c), contextlib.redirect_stdout(io.StringIO()):
            code = bw.cmd_review(args)
        self.assertEqual(code, 2, 'Evidence-only review must not silently exit success on a drafts-only scope')

if __name__ == '__main__':
    unittest.main(verbosity=2)
