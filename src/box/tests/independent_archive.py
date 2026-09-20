"""Independent offline regression checks against a Muse archive's Box CLI.

Usage: python3 tests/review_archive.py path/to/box/bin/box
No Box requests or real credentials are used. API compatibility differences must
be inspected rather than counted as passing checks.
"""
import importlib.machinery
import importlib.util
import io
import argparse
import contextlib
import json
import sys
import types
import unittest
import zipfile
from unittest.mock import patch

source = sys.argv.pop(1)
sys.modules['dynamic_credentials'] = types.SimpleNamespace(
    add_surrogate_to_request=lambda *a, **k: None,
    read_response_body=lambda response: response.read())
loader = importlib.machinery.SourceFileLoader('reviewed_box', source)
spec = importlib.util.spec_from_loader(loader.name, loader)
cli = importlib.util.module_from_spec(spec)
loader.exec_module(cli)

class IndependentReview(unittest.TestCase):
    def test_lost_post_response_is_not_replayed(self):
        calls = []
        class LostResponse:
            def open(self, request, **kwargs):
                calls.append(request.get_method())
                raise TimeoutError('response lost after possible commit')
        with patch.object(cli, 'opener', return_value=LostResponse()), patch.object(cli.time, 'sleep'):
            with patch.object(cli, 'reconcile_create_folder', return_value={'status': 'not_found'}, create=True), contextlib.redirect_stdout(io.StringIO()):
                cli.cmd_create_folder(argparse.Namespace(name='fixture', parent_id='123'))
        self.assertEqual(calls, ['POST'], 'A possibly committed mutation must be reconciled before retry')

    def test_png_is_not_extracted_as_text(self):
        result = cli.extract_text(b'\x89PNG\r\n\x1a\n\xff', 'image/png', 'image.png')
        if 'status' in result:
            self.assertEqual(result['status'], 'unsupported')
        else:
            self.assertFalse(result['extracted'])

    def test_docx_entities_are_decoded(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('word/document.xml',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>A &amp; B</w:t></w:r></w:p></w:body></w:document>')
        result = cli.extract_text(data.getvalue(),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'fixture.docx')
        self.assertEqual(result['text'].strip(), 'A & B')

    def test_structured_error_redacts_signed_url(self):
        marker = 'SYNTHETIC_SECRET_123'
        result = cli.actionable_error(403, json.dumps({'context_info': {'url': 'https://dl.boxcloud.com/d/' + marker}}).encode(), 'read')
        self.assertNotIn(marker, json.dumps(result))

    def test_mismatched_content_is_not_verified(self):
        metadata = {'id': '123', 'name': 'fixture.txt', 'size': 5,
                    'sha1': '0' * 40, 'file_version': {'id': '7'}}
        output = io.StringIO()
        with patch.object(cli, 'get_metadata', return_value=(200, json.dumps(metadata).encode(), {})), patch.object(cli, 'download_content', return_value=(True, {'bytes': b'wrong', 'content_type': 'text/plain'})), contextlib.redirect_stdout(output):
            result = cli.cmd_read_file(argparse.Namespace(file_id='123', text=True, out=None))
        body = json.loads(output.getvalue())
        self.assertFalse(body['ok'])
        self.assertNotEqual(result, 0)

if __name__ == '__main__':
    unittest.main()
