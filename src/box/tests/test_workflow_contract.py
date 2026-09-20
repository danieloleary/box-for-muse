"""Cross-module regressions using synthetic Box responses and real workflow code."""
import importlib.util
import json
from pathlib import Path
import unittest
from urllib.parse import urlparse, parse_qs

spec = importlib.util.spec_from_file_location('workflow_contract', Path(__file__).resolve().parents[1] / 'workflows.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class Fake:
    API_BASE = 'https://api.box.com/2.0'
    valid_id = staticmethod(lambda value: str(value).isdigit())
    def __init__(self, pages, text='', status='ok'):
        self.pages, self.text, self.status, self.offsets = pages, text, status, []
    def do_request(self, url):
        offset = int(parse_qs(urlparse(url).query)['offset'][0])
        self.offsets.append(offset)
        page = self.pages.get(offset, self.pages[0])
        return 200, json.dumps(page).encode(), {}
    def cmd_read_file(self, args):
        print(json.dumps({'ok': True, 'version': {'verified': True, 'file_version_id': '8', 'sha1': 'synthetic'},
                          'extraction': {'text': self.text, 'status': self.status, 'truncated': False}}))
        return 0

def file(name='notes.docx'):
    return {'id': '7', 'type': 'file', 'name': name, 'file_version': {'id': '8'}}

def page(entries, offset=0, limit=2, total=1):
    return dict(entries=entries, offset=offset, limit=limit, total_count=total)

class WorkflowContract(unittest.TestCase):
    def test_sparse_page_does_not_hide_later_file(self):
        c = Fake({0: page([], total=3), 2: page([file()], offset=2, total=3)})
        files, coverage = w.traverse_folders(c, '9', page_limit=2)
        self.assertEqual(c.offsets, [0, 2])
        self.assertEqual([f['entry']['id'] for f in files], ['7'])
        self.assertTrue(coverage['complete'])
    def test_missing_total_is_incomplete(self):
        _, coverage = w.traverse_folders(Fake({0: {'entries': []}}), '9')
        self.assertFalse(coverage['complete'])
    def test_repeated_response_offset_is_incomplete(self):
        c = Fake({0: page([file()], total=5)})
        _, coverage = w.traverse_folders(c, '9', page_limit=2)
        self.assertFalse(coverage['complete'])
        self.assertEqual(c.offsets, [0, 2])
    def test_partial_docx_cannot_confirm_customer(self):
        c = Fake({0: page([file()])}, 'Customer Cedar Works', 'partial')
        result = w.gather_customer_files(c, '9', [{'name': 'Cedar', 'aliases': ['Cedar Works'], 'cases': []}])
        self.assertEqual(result['confirmed_files'], [])
        self.assertEqual(len(result['ambiguous_files']), 1)
    def test_partial_docx_cannot_confirm_expiration(self):
        c = Fake({0: page([file('Partner contract.docx')])}, 'This contract expires December 31, 2027.', 'partial')
        result = w.review_contracts(c, '9', 2027)
        self.assertEqual(result['expiring_in_year'], [])
        self.assertEqual(len(result['needs_review']), 1)

if __name__ == '__main__':
    unittest.main()
