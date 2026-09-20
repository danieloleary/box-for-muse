"""Independent release oracles; no network, credentials, or private fixtures.
Run: python3 review/war-council/code/test_release_edges.py [path-to-box-dir]
"""
import argparse, contextlib, hashlib, importlib.machinery, importlib.util, io, json
from pathlib import Path
import socket, sys, tempfile, types, unittest
from unittest.mock import patch
from email.parser import BytesParser
from email import policy
ROOT=Path(sys.argv.pop(1)) if len(sys.argv)>1 else Path('implementation/integrated-v7/box')
def deny(*a,**kw): raise AssertionError('Network/credentials forbidden')
socket.socket.connect=deny
socket.create_connection=deny
dc=types.ModuleType('dynamic_credentials');dc.add_surrogate_to_request=deny;dc.read_response_body=lambda r:r.read();sys.modules['dynamic_credentials']=dc
def load(name,path):
 loader=importlib.machinery.SourceFileLoader(name,str(path));spec=importlib.util.spec_from_loader(name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m);return m
box=load('edge_box',ROOT/'bin/box');w=load('edge_workflow',ROOT/'workflows.py')
def response(v): return 200,json.dumps(v).encode(),{}
def invoke(fn,**kw):
 out=io.StringIO()
 with contextlib.redirect_stdout(out): code=fn(argparse.Namespace(**kw))
 return code,json.loads(out.getvalue())
class Fake:
 API_BASE='https://api.box.com/2.0'; valid_id=staticmethod(lambda s:s.isdigit())
 def __init__(self,denied=False):self.denied=denied
 def do_request(self,url):return response({'entries':[{'id':'101','type':'file','name':'notes.txt','file_version':{'id':'old-v'},'sha1':'old-hash','size':10}],'offset':0,'limit':100,'total_count':1})
 def cmd_read_file(self,args):
  if self.denied: print(json.dumps({'ok':False,'status':403}));return 1
  print(json.dumps({'ok':True,'version':{'file_version_id':'new-v','sha1':'new-hash','size':20,'verified':True},'extraction':{'status':'ok','text':'Cedar Works','truncated':False}}));return 0
class ReleaseEdges(unittest.TestCase):
 def test_denied_content_is_unassessed_not_complete_no_match(self):
  r=w.gather_customer_files(Fake(True),'10',[{'name':'Cedar','aliases':['Cedar Works'],'cases':[]}])
  self.assertFalse(r['coverage']['complete'], 'Unreadable required evidence cannot support complete search')
  self.assertEqual(['101'],[f['file_id'] for f in r['unassessed_files']])
 def test_content_match_cites_read_version_not_older_listing(self):
  r=w.gather_customer_files(Fake(),'10',[{'name':'Cedar','aliases':['Cedar Works'],'cases':[]}])
  record=r['confirmed_files'][0]
  sources=[record.get('source',{}),record.get('content_source',{}),record.get('evidence_source',{})]
  self.assertTrue(any(s.get('file_version_id')=='new-v' for s in sources), 'Match came from new-v but only old-v is cited')
 def test_malformed_metadata_after_accepted_upload_is_ambiguous_json(self):
  with tempfile.NamedTemporaryFile() as f:
   f.write(b'hello');f.flush()
   with patch.object(box,'do_request',return_value=response({'entries':[{'id':'101','name':'notes.txt'}]})),patch.object(box,'get_metadata',return_value=(200,b'not-json',{})):
    code,out=invoke(box.cmd_save_document,local_path=f.name,parent_id='10',name='notes.txt')
   self.assertEqual(code,2);self.assertTrue(out['ambiguous']);self.assertFalse(out['ok'])
 def test_accepted_upload_invalid_id_does_not_build_metadata_url(self):
  with tempfile.NamedTemporaryFile() as f:
   f.write(b'hello');f.flush()
   with patch.object(box,'do_request',return_value=response({'entries':[{'id':'../users/me?fields=login','name':'notes.txt'}]})),patch.object(box,'get_metadata',side_effect=AssertionError('invalid provider ID used for request URL')):
    code,out=invoke(box.cmd_save_document,local_path=f.name,parent_id='10',name='notes.txt')
   self.assertEqual(code,2);self.assertTrue(out['ambiguous'])
 def test_multipart_quoted_filename_is_preserved(self):
  requests=[];name='customer "approved".txt'
  def capture(url,**kw):requests.append(kw);return 403,b'{}',{}
  with tempfile.NamedTemporaryFile() as f:
   f.write(b'hello');f.flush()
   with patch.object(box,'do_request',side_effect=capture):invoke(box.cmd_save_document,local_path=f.name,parent_id='10',name=name)
  req=requests[0];msg=BytesParser(policy=policy.default).parsebytes(('Content-Type: '+req['content_type']+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+req['data'])
  self.assertEqual(list(msg.iter_parts())[1].get_filename(),name)
 def test_multipart_preserves_arbitrary_file_bytes(self):
  data=b'prefix\r\n------boxcli7f3a9c2e\r\nContent-Disposition: form-data; name="surprise"\r\n\r\nsuffix'
  requests=[]
  def capture(url,**kw): requests.append(kw);return 403,b'{}',{}
  with tempfile.NamedTemporaryFile() as f:
   f.write(data);f.flush()
   with patch.object(box,'do_request',side_effect=capture):invoke(box.cmd_save_document,local_path=f.name,parent_id='10',name='notes.txt')
  req=requests[0];msg=BytesParser(policy=policy.default).parsebytes(('Content-Type: '+req['content_type']+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+req['data'])
  parts=list(msg.iter_parts());self.assertEqual(len(parts),2,'file bytes were parsed as an extra multipart field')
  self.assertEqual(parts[1].get_payload(decode=True),data)
if __name__=='__main__':unittest.main(verbosity=2)
