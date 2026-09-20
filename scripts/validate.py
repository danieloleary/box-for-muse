import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'data/use-cases.json').read_text())
assert len(data)==50, 'Expected 50 use cases'
assert len({x['id'] for x in data})==50, 'Duplicate ID'
assert sorted(x['rank'] for x in data)==list(range(1,51)), 'Invalid ranks'
sources=(root/'research/SOURCES.md').read_text()
for x in data:
    for k in ['title','category','trigger','output','guardrail','acceptance','attribution','last_reviewed']:
        assert x.get(k), (x['id'],k)
    assert x['dependency'] in ['core','events','metadata','ai','admin']
    assert all('## '+s in sources for s in x['source_ids']), x['id']
for p in root.rglob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if not link.startswith(('https://','http://','#')):
            assert (p.parent/link.split('#')[0]).exists(), (p,link)
assert (root/'USE-CASES.md').read_text().count('| **')==50
print('PASS: 50 unique cases, ordered ranks, required fields, source references and local links')
