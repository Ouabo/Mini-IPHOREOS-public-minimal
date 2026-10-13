"""Check PDF layout and local links for the mathematical companion."""
from pathlib import Path
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[1]
doc = fitz.open(ROOT / 'Mathematical_Model.pdf')
report = {'pages': len(doc), 'words': 0, 'outside_page_blocks': [], 'local_links': [], 'hardware_tested': False}
for i, page in enumerate(doc):
    report['words'] += len(page.get_text().split())
    for b in page.get_text('blocks'):
        if b[0] < -1 or b[1] < -1 or b[2] > page.rect.width + 1 or b[3] > page.rect.height + 1:
            report['outside_page_blocks'].append(i+1)
    for link in page.get_links():
        target = link.get('file', '')
        if not target:
            continue
        name, _, fragment = target.partition('#')
        assert (ROOT / name).is_file(), target
        if fragment and name.endswith('.html'):
            assert 'id="' + fragment + '"' in (ROOT / name).read_text(encoding='utf-8'), target
        report['local_links'].append(target)
    if i in (0, 4, 6, len(doc)-2, len(doc)-1):
        page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(ROOT / 'review' / f'math_{i+1:02}.png')
assert not report['outside_page_blocks']
log = (ROOT / 'Mathematical_Model.log').read_text(encoding='utf-8', errors='replace')
assert 'Overfull' not in log and 'undefined' not in log
guide = (ROOT / 'Tutorial_A_to_Z.html').read_text(encoding='utf-8')
assert 'href="Mathematical_Model.pdf"' in guide
assert len(re.findall(r'id="t\d\d"', guide)) == 24
report['local_links'] = sorted(set(report['local_links']))
(ROOT / 'review/math_verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
