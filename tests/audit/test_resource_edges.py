"""Proposed release bounds: 20 MiB files, 8 MiB DOCX document.xml.
These are connector limits, not Box platform limits. Never allocates huge files.
Run with a box-directory argument; uses helper from test_release_edges.
"""
import unittest, io, zipfile
from unittest.mock import patch
import test_release_edges as e
class ResourceEdges(unittest.TestCase):
 def test_metadata_oversize_prevents_download(self):
  size=20*1024*1024+1
  metadata={'id':'101','name':'large.txt','size':size,'sha1':'a'*40,'file_version':{'id':'1'}}
  with patch.object(e.box,'get_metadata',return_value=e.response(metadata)),patch.object(e.box,'download_content',return_value=(False,{'ok':False,'reason':'test sentinel'})) as download:
   code,out=e.invoke(e.box.cmd_read_file,file_id='101',out=None,text=True)
  download.assert_not_called();self.assertNotEqual(code,0);self.assertFalse(out['ok'])
 def test_docx_expansion_rejected_before_materializing_xml(self):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w',compression=zipfile.ZIP_DEFLATED) as z:
   z.writestr('word/document.xml', b'<document>'+b' '*(8*1024*1024)+b'</document>')
  self.assertLess(len(data.getvalue()),10000)
  with patch.object(zipfile.ZipFile,'read',side_effect=AssertionError('oversize member materialized before size gate')):
   result=e.box._extract_docx(data.getvalue())
  self.assertEqual(result['status'],'failed')
  self.assertNotIn('materialized before size gate',result.get('hint',''))
if __name__=='__main__':unittest.main(verbosity=2)
