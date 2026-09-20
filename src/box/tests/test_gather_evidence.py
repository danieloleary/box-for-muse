"""Synthetic acceptance of opt-in cached evidence; no Box calls."""
import importlib.util
import importlib.machinery
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('gather_evidence_workflows', Path(__file__).resolve().parents[1] / 'workflows.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class Fake:
    API_BASE = 'https://api.box.com/2.0'
    valid_id = staticmethod(lambda value: str(value).isdigit())
    def __init__(self, texts, status='ok', verified=True, named=False, uncertain=False):
        self.texts, self.status, self.verified = texts, status, verified
        self.named, self.uncertain, self.read_calls = named, uncertain, []
    def do_request(self, url):
        entries = [{'id': str(i), 'type': 'file', 'name': 'Cedar Works.txt' if self.named else 'notes.txt',
                    'sha1': 'listed', 'file_version': {'id': 'old'}} for i in range(len(self.texts))]
        return 200, json.dumps({'entries': entries, 'total_count': len(entries), 'limit': 100, 'offset': 0}).encode(), {}
    def cmd_read_file(self, args):
        self.read_calls.append(args.file_id)
        text = self.texts[int(args.file_id)]
        data = {'ok': True, 'version': {'verified': self.verified, 'file_version_id': 'read-v', 'sha1': 'read-sha'},
                'extraction': {'status': self.status, 'text': text, 'truncated': False,
                               'total_length': len(text), 'limits': ['headers omitted'] if self.status == 'partial' else []}}
        if self.uncertain:
            data['version_check_note'] = 'current version unknown'
        print(json.dumps(data))
        return 0

CUSTOMERS = [{'name': 'Cedar', 'aliases': ['Cedar Works'], 'cases': []},
             {'name': 'Partner', 'aliases': ['PartnerCo'], 'cases': []}]

def gather(fake, enabled=True):
    return w.gather_customer_files(fake, '9', CUSTOMERS, include_evidence=enabled)

def records(result):
    return sum((result[k] for k in ('confirmed_files', 'ambiguous_files', 'unmatched_files', 'unassessed_files')), [])

class GatherEvidence(unittest.TestCase):
    def test_reuses_one_read_per_file_across_customers(self):
        c = Fake(['Cedar Works and PartnerCo'])
        r = gather(c)
        self.assertEqual(c.read_calls, ['0'])
        e = records(r)[0]['evidence']
        self.assertEqual(e['text'], 'Cedar Works and PartnerCo')
        self.assertEqual(e['source']['file_version_id'], 'read-v')
        self.assertTrue(e['complete'])

    def test_default_returns_no_new_output_fields(self):
        r = gather(Fake(['Cedar Works']), False)
        self.assertNotIn('evidence_summary', r)
        self.assertNotIn('evidence', records(r)[0])

    def test_partial_verified_text_is_labelled_and_not_confirmed(self):
        r = gather(Fake(['Cedar Works'], status='partial'))
        self.assertEqual(r['confirmed_files'], [])
        e = records(r)[0]['evidence']
        self.assertEqual(e['text'], 'Cedar Works')
        self.assertEqual(e['extraction']['status'], 'partial')
        self.assertFalse(e['complete'])
        self.assertFalse(r['coverage']['complete'])

    def test_unverified_and_uncertain_text_never_returned(self):
        for kwargs in ({'verified': False}, {'uncertain': True}):
            with self.subTest(kwargs=kwargs):
                r = gather(Fake(['PRIVATE_TEST_SENTINEL'], **kwargs))
                self.assertNotIn('PRIVATE_TEST_SENTINEL', json.dumps(r))
                self.assertFalse(records(r)[0]['evidence']['available'])

    def test_strict_utf8_per_file_and_total_caps_report_incomplete(self):
        c = Fake(['Cedar Works ' + '😀' * 4000] * 6)
        r = gather(c)
        evidence = [rec['evidence'] for rec in records(r)]
        sizes = [len(e['text'].encode('utf-8')) for e in evidence]
        self.assertTrue(all(n <= w.EVIDENCE_PER_FILE_BYTES for n in sizes))
        self.assertLessEqual(sum(sizes), w.EVIDENCE_TOTAL_BYTES)
        self.assertEqual(r['evidence_summary']['text_bytes'], sum(sizes))
        self.assertFalse(r['evidence_summary']['complete'])
        self.assertFalse(r['coverage']['complete'])
        self.assertTrue(all(e['output_truncated'] for e in evidence))
        self.assertEqual(len(c.read_calls), 6)

    def test_filename_match_does_not_add_download(self):
        c = Fake(['Cedar Works'], named=True)
        r = w.gather_customer_files(c, '9', CUSTOMERS[:1], include_evidence=True)
        self.assertEqual(c.read_calls, [])
        self.assertFalse(records(r)[0]['evidence']['available'])
        self.assertFalse(r['evidence_summary']['complete'])

    def test_cli_flag_returns_evidence_and_cap_exit_two(self):
        loader = importlib.machinery.SourceFileLoader('evidence_boxwork', str(Path(__file__).resolve().parents[1] / 'bin/boxwork'))
        bw = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
        with patch.dict(sys.modules, {'workflows': w}):
            loader.exec_module(bw)
        c = Fake(['Cedar Works ' + 'x' * 10000])
        output = io.StringIO()
        args = ['boxwork', 'gather-customer-files', '--folder-id', '9', '--customer', 'Cedar',
                '--alias', 'Cedar Works', '--include-evidence']
        with patch.object(w, 'load_cli', return_value=c), patch.object(sys, 'argv', args), contextlib.redirect_stdout(output):
            code = bw.main()
        self.assertEqual(code, 2)
        r = json.loads(output.getvalue())
        self.assertEqual(records(r)[0]['evidence']['text_bytes'], w.EVIDENCE_PER_FILE_BYTES)
        self.assertEqual(c.read_calls, ['0'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
