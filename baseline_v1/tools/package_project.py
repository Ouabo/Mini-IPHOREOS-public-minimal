"""Create a portable source-and-documentation archive, excluding local caches."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / 'Mini_IPHOREOS_Starter_Project.zip'
SKIP = {'__pycache__', '.pytest_cache', '.git', '.venv'}

def included(path):
    relative = path.relative_to(ROOT)
    return (path.is_file() and not any(p in SKIP for p in relative.parts)
            and not (relative.parts[0] == 'review' and path.suffix == '.png')
            and path.name != 'PROJECT_MANIFEST.json'
            and path.suffix not in {'.aux', '.log', '.toc', '.out', '.synctex'})

files = sorted(p for p in ROOT.rglob('*') if included(p))
manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files}
manifest_path = ROOT / 'PROJECT_MANIFEST.json'
manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in files + [manifest_path]:
        archive.write(path, 'Mini_IPHOREOS/' + path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(OUTPUT) as archive:
    assert archive.testzip() is None
    for name, expected in manifest.items():
        assert hashlib.sha256(archive.read('Mini_IPHOREOS/' + name)).hexdigest() == expected
print(f'{OUTPUT}\n{len(files)+1} files; {OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB; CRC and SHA-256 checks passed.')
