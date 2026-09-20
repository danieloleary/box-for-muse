"""Independent RC8 transport oracles; fake response objects only."""
import http.client, io, json, tempfile, unittest, urllib.error
from unittest.mock import patch
import test_release_edges as e
class RecordingBody(io.BytesIO):
 def __init__(self,data):super().__init__(data);self.requests=[]
 def read(self,n=-1):self.requests.append(n);return super().read(n)
class BoundedTransport(unittest.TestCase):
 def test_exact_limit_returns_all_bytes(self):
  body=RecordingBody(b'a'*123)
  self.assertEqual(e.box.read_bounded_response(body,123),b'a'*123)
  self.assertTrue(all(0<n<=124 for n in body.requests))
  self.assertEqual(body.tell(),123)
 def test_oversize_consumes_only_limit_plus_one(self):
  body=RecordingBody(b'a'*1000)
  with self.assertRaises(e.box.ResponseLimitError):e.box.read_bounded_response(body,123)
  self.assertEqual(body.tell(),124)
  self.assertEqual(body.requests,[124])
 def test_chunk_bound_applies_to_unknown_large_stream(self):
  body=RecordingBody(b'a'*200000)
  with self.assertRaises(e.box.ResponseLimitError):e.box.read_bounded_response(body,100000)
  self.assertEqual(body.tell(),100001)
  self.assertEqual(body.requests,[65536,34465])
 def test_read_failure_is_not_truncated_success(self):
  body=unittest.mock.Mock();body.read.side_effect=[b'partial',OSError('read failed')]
  with self.assertRaises(OSError):e.box.read_bounded_response(body,123)
 def test_mutation_response_limit_is_ambiguous_not_provider_413(self):
  with tempfile.NamedTemporaryFile() as f:
   f.write(b'hello');f.flush()
   with patch.object(e.box,'build_request',return_value=object()),patch.object(e.box,'_http_open',side_effect=e.box.ResponseLimitError('large response')) as transport,patch.object(e.box,'reconcile_save_document',return_value={'outcome':'not_found'}):
    code,out=e.invoke(e.box.cmd_save_document,local_path=f.name,parent_id='10',name='notes.txt')
   self.assertEqual(transport.call_count,1)
   self.assertEqual(code,2);self.assertTrue(out['ambiguous']);self.assertFalse(out['ok'])
 def test_chunked_incomplete_mutation_is_ambiguous_without_retry(self):
  with tempfile.NamedTemporaryFile() as f:
   f.write(b'hello');f.flush()
   with patch.object(e.box,'build_request',return_value=object()),patch.object(e.box,'_http_open',side_effect=http.client.IncompleteRead(b'partial',10)) as transport,patch.object(e.box,'reconcile_save_document',return_value={'outcome':'not_found'}):
    code,out=e.invoke(e.box.cmd_save_document,local_path=f.name,parent_id='10',name='notes.txt')
   self.assertEqual(transport.call_count,1)
   self.assertEqual(code,2);self.assertTrue(out['ambiguous'])
 def test_error_body_read_failure_preserves_status_without_crash(self):
  stream=unittest.mock.Mock();stream.read.side_effect=OSError('interrupted error body')
  error=urllib.error.HTTPError('https://api.box.com/2.0/users/me',403,'forbidden',{},stream)
  with patch.object(e.box,'build_request',return_value=object()),patch.object(e.box,'_http_open',side_effect=error) as transport:
   status,body,_=e.box.do_request(e.box.API_BASE+'/users/me')
  self.assertEqual(status,403);self.assertEqual(transport.call_count,1)
  self.assertIsInstance(json.loads(body),dict)
if __name__=='__main__':unittest.main(verbosity=2)
