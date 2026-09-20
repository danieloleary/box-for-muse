"""Independent package boundary assertions against the generated archive."""
import hashlib
import importlib.util
from pathlib import Path
import tarfile
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_release.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

class Packaging(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'rc.tar.gz'; b.build(destination=self.path)
    def test_only_four_production_files_and_release_documents(self):
        with tarfile.open(self.path) as t:
            self.assertEqual(set(t.getnames()), {'box/SKILL.md','box/workflows.py','box/bin/box','box/bin/boxwork','README.md','RELEASE.json','MANIFEST.sha256','LICENSE','NOTICE'})
            self.assertTrue(all(m.isfile() for m in t.getmembers()))
    def test_current_source_byte_identity(self):
        with tarfile.open(self.path) as t:
            for n in b.INSTALL_FILES:
                self.assertEqual(t.extractfile('box/'+n).read(), (ROOT/'src/box'/n).read_bytes())
    def test_every_payload_member_is_integrity_checked(self):
        with tarfile.open(self.path) as t:
            lines = t.extractfile('MANIFEST.sha256').read().decode().splitlines()
            checked = set()
            for line in lines:
                digest, name = line.split('  ',1); checked.add(name)
                self.assertEqual(hashlib.sha256(t.extractfile(name).read()).hexdigest(), digest)
            self.assertEqual(checked, set(t.getnames())-{'MANIFEST.sha256'})
    def test_build_is_reproducible(self):
        first=self.path.read_bytes(); b.build(destination=self.path)
        self.assertEqual(first,self.path.read_bytes())

if __name__=='__main__': unittest.main()
