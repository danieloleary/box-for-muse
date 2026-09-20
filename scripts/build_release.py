#!/usr/bin/env python3
"""Build a deterministic, allowlisted Muse installation archive. No credentials."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
INSTALL_FILES = ('SKILL.md', 'workflows.py', 'bin/box', 'bin/boxwork')


def build(root=ROOT, destination=None):
    root = Path(root)
    destination = Path(destination or root / 'dist/box-for-muse-rc9.tar.gz')
    contents = {}
    for relative in INSTALL_FILES:
        p = root / 'src/box' / relative
        if p.is_symlink() or not p.is_file():
            raise ValueError('missing or symlinked release source: ' + relative)
        contents['box/' + relative] = p.read_bytes()
    for document in ('LICENSE', 'NOTICE'):
        contents[document] = (root / document).read_bytes()
    contents['RELEASE.json'] = (json.dumps({
        'name': 'Box for Muse', 'version': '0.1.0-rc9',
        'community_connector': True, 'directory_submitted': False,
        'install_path': '~/workspace/skills/box/',
        'license': 'Apache-2.0',
        'limits': {'file_bytes': 20 * 1024 * 1024, 'docx_xml_bytes': 8 * 1024 * 1024},
        'contract_review': 'evidence only; not definitive expiration',
    }, indent=2) + '\n').encode()
    contents['README.md'] = b'''# Box for Muse RC9\n\nPrivate review candidate, not a published release.\n\nVerify MANIFEST.sha256 before installation. Preserve the previous skill for rollback.\nInstall only box/ into ~/workspace/skills/box/. Do not install the QA bundle there.\nRequires Python 3, Muse platform dynamic_credentials helper and connected custom.box.\nPDF extraction additionally requires pdftotext.\n\nEach user must connect their own grant and follow their own runtime approvals.\nNo personal authorization, tests, test credentials, receipts or document bodies are included.\nContent downloaded from Box enters Muse runtime and may be processed there. The connector\ndoes not implement Box retention or watermark controls on downloaded copies.\n\nSearch/read/customer gathering are implemented. Save verification exists but release\nreadiness requires a live Muse save/readback receipt. Refresh and restart evidence are\nseparate unresolved release checks. Contract review returns candidates requiring review.\nBox AI, Hubs and background monitoring are not included.\n\nSupport contact, public privacy terms and directory requirements must be\nresolved before public distribution. Nothing in this package claims Box or Meta endorsement.\n'''
    contents['MANIFEST.sha256'] = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
                                           for name, data in sorted(contents.items())).encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('wb') as out:
        with gzip.GzipFile(filename='', fileobj=out, mode='wb', mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode='w') as archive:
                for name, data in sorted(contents.items()):
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    info.mode = 0o755 if name.startswith('box/bin/') else 0o644
                    info.mtime = 0
                    archive.addfile(info, io.BytesIO(data))
    receipt = {'artifact': str(destination), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
               'members': sorted(contents), 'production_sha256': {
                   name: hashlib.sha256(data).hexdigest() for name, data in contents.items() if name.startswith('box/')}}
    destination.with_suffix(destination.suffix + '.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
