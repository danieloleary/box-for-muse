"""Redirect transport regressions. Synthetic responses; never grants access."""
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import sys
import types
import unittest
import urllib.error
from unittest.mock import patch

stub = types.ModuleType('dynamic_credentials')
stub.add_surrogate_to_request = lambda *a, **k: (_ for _ in ()).throw(AssertionError('unexpected auth access'))
stub.read_response_body = lambda response: response.read()
sys.modules['dynamic_credentials'] = stub
loader = importlib.machinery.SourceFileLoader('redirect_diagnostic_box', str(Path(__file__).resolve().parents[1] / 'bin/box'))
spec = importlib.util.spec_from_loader(loader.name, loader)
box = importlib.util.module_from_spec(spec)
loader.exec_module(box)
REDIRECT = (302, b'', {'location': 'https://dl.boxcloud.com/signed?token=synthetic-secret'})

class RedirectDiagnostics(unittest.TestCase):
    def test_timeout_reports_one_redirect_attempt_without_replay(self):
        with patch.object(box, 'do_request', return_value=REDIRECT), patch.object(box, '_follow_open', side_effect=TimeoutError('timed out')) as follow, patch.object(box.time, 'monotonic', side_effect=[10, 70]), patch.object(box.time, 'sleep') as sleep:
            ok, result = box.download_content('123')
        self.assertFalse(ok)
        self.assertEqual(follow.call_count, 1)
        sleep.assert_not_called()
        request, timeout = follow.call_args.args
        self.assertFalse(request.has_header('Authorization'))
        self.assertEqual(timeout, 60)
        self.assertEqual(result['transport'], {'stage': 'redirected_download', 'error_kind': 'timeout', 'attempts': 1, 'timeout_seconds': 60, 'elapsed_seconds': 60, 'automatic_retry': False})
        self.assertIn('approval', result['guidance'])
        self.assertNotIn('synthetic-secret', str(result))

    def test_urlerror_timeout_is_distinguished_from_other_transport_failure(self):
        for error, expected in [(urllib.error.URLError(TimeoutError('timed out')), 'timeout'), (urllib.error.URLError('connection reset'), 'transport')]:
            with self.subTest(expected=expected), patch.object(box, 'do_request', return_value=REDIRECT), patch.object(box, '_follow_open', side_effect=error):
                ok, result = box.download_content('123')
                self.assertFalse(ok)
                self.assertEqual(result['transport']['error_kind'], expected)

    def test_exception_signed_urls_stay_redacted(self):
        with patch.object(box, 'do_request', return_value=REDIRECT), patch.object(box, '_follow_open', side_effect=TimeoutError('failed https://dl.boxcloud.com/private?token=secret-value')):
            ok, result = box.download_content('123')
        self.assertFalse(ok)
        self.assertNotIn('secret-value', str(result))
        self.assertNotIn('/private', str(result))

    def test_provider_denial_closes_body_and_does_not_retry(self):
        body = io.BytesIO(b'do not expose')
        error = urllib.error.HTTPError(REDIRECT[2]['location'], 403, 'denied', {}, body)
        with patch.object(box, 'do_request', return_value=REDIRECT), patch.object(box, '_follow_open', side_effect=error) as follow:
            ok, result = box.download_content('123')
        self.assertFalse(ok)
        self.assertEqual(result['status'], 403)
        self.assertTrue(body.closed)
        self.assertEqual(follow.call_count, 1)
        self.assertNotIn('synthetic-secret', str(result))

    def test_size_limit_is_not_mislabeled_as_timeout(self):
        with patch.object(box, 'do_request', return_value=REDIRECT), patch.object(box, '_follow_open', side_effect=box.ResponseLimitError('response exceeds connector byte limit')):
            ok, result = box.download_content('123')
        self.assertFalse(ok)
        self.assertEqual(result['transport']['error_kind'], 'response_limit')

if __name__ == '__main__':
    unittest.main(verbosity=2)
