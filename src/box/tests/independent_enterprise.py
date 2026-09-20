"""Independent workflow acceptance. Synthetic transport only."""
import importlib.util,json,sys,unittest
from urllib.parse import urlparse
spec=importlib.util.spec_from_file_location('workflows',sys.argv.pop(1));w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
class Fake:
 API_BASE='https://api.box.com/2.0'
 valid_id=staticmethod(lambda x: str(x).isdigit())
 def __init__(self,folders,texts=None): self.folders=folders;self.texts=texts or {}
 def do_request(self,url):
  fid=urlparse(url).path.split('/')[3]; rows=self.folders.get(fid)
  return (403,b'{}',{}) if rows is None else (200,json.dumps({'entries':rows,'total_count':len(rows)}).encode(),{})
 def cmd_read_file(self,args):
  text=self.texts.get(args.file_id,'No customer evidence.')
  print(json.dumps({'ok':True,'version':{'file_version_id':'1','sha1':'synthetic','verified':True},'extraction':{'status':'ok','text':text,'truncated':False}}));return 0

def gather(c,folder,identifiers):
 if hasattr(w,'_parse_customer_tokens'):
  customers=[{'name':'target','aliases':[x['value'] for x in identifiers if x['kind']=='alias'],'cases':[x['value'] for x in identifiers if x['kind']=='case_id']}]
  result=w.gather_customer_files(c,folder,customers)
  result['matched_files']=result['confirmed_files']
  return result
 return w.gather_customer_files(c,folder,identifiers)

def file(i,name): return {'id':i,'type':'file','name':name,'file_version':{'id':'1'}}
class Acceptance(unittest.TestCase):
 def test_nested_customer_file(self):
  c=Fake({'10':[{'id':'11','type':'folder','name':'customer'}],'11':[file('101','Cedar Works CW-104 proposal')]})
  r=gather(c,'10',[{'kind':'alias','value':'Cedar Works'},{'kind':'case_id','value':'CW-104'}])
  self.assertIn('101',[f['file_id'] for f in r['matched_files']])
 def test_similar_customer_not_confirmed(self):
  c=Fake({'10':[file('102','Cedar Workshop CW-104 proposal')]})
  r=gather(c,'10',[{'kind':'alias','value':'Cedar Works'},{'kind':'case_id','value':'CW-104'}])
  self.assertEqual([],r['matched_files'])
 def test_failed_child_is_incomplete(self):
  c=Fake({'10':[{'id':'11','type':'folder','name':'restricted'}]})
  r=gather(c,'10',[{'kind':'alias','value':'Cedar Works'}])
  self.assertFalse(r['coverage']['complete'])
 def test_amendment_prevents_definitive_old_expiry(self):
  c=Fake({'10':[file('201','partner agreement'),file('202','partner agreement amendment')]},{'201':'This agreement expires December 31, 2027.','202':'The parties extend the expiration date of agreement 201 to December 31, 2028.'})
  r=w.review_contracts(c,'10',2027)
  self.assertEqual([],r['expiring_in_year'])
 def test_file_limit_incomplete(self):
  c=Fake({'10':[file('201','contract'),file('202','contract')]},{'201':'Expires December 31, 2027.'})
  r=w.review_contracts(c,'10',2027,max_files=1)
  self.assertFalse(r['coverage']['complete'])
 def test_invalid_calendar_date_not_candidate(self):
  signals=w.extract_contract_signals('This contract expires February 30, 2027.')
  self.assertNotIn('2027-02-30',signals['candidate_expiration_dates'])
 def test_generic_filename_matched_by_content(self):
  c=Fake({'10':[file('101','notes.txt')]},{'101':'Customer: Cedar Works. Case: CW-104. Meeting decisions.'})
  r=gather(c,'10',[{'kind':'alias','value':'Cedar Works'},{'kind':'case_id','value':'CW-104'}])
  self.assertIn('101',[f['file_id'] for f in r['matched_files']])
 def test_content_cache_does_not_transfer_customer_match(self):
  if not hasattr(w,'_parse_customer_tokens'): self.skipTest('multiple customer groups added in v5')
  c=Fake({'10':[file('101','notes.txt')]},{'101':'Customer: Cedar Works. Case: CW-104.'})
  customers=[{'name':'Cedar','aliases':['Cedar Works'],'cases':['CW-104']},{'name':'Other','aliases':['Other Company'],'cases':['OTHER-99']}]
  r=w.gather_customer_files(c,'10',customers)
  self.assertEqual(['Cedar'],r['confirmed_files'][0]['matched_customers'])
 def test_name_alias_plus_content_case(self):
  c=Fake({'10':[file('101','Cedar Works notes.txt')]},{'101':'Customer: Cedar Works. Case: CW-104.'})
  r=gather(c,'10',[{'kind':'alias','value':'Cedar Works'},{'kind':'case_id','value':'CW-104'}])
  self.assertIn('101',[f['file_id'] for f in r['matched_files']])
if __name__=='__main__': unittest.main()
