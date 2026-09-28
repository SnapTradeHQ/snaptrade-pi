"""Package an explicit, secret-free allowlist for the public DIY download."""
from pathlib import Path
import hashlib
import zipfile

root = Path(__file__).resolve().parents[1]
out = root / 'landing/dist/downloads'
out.mkdir(parents=True, exist_ok=True)
archive = out / 'snaptrade-pi-diy-v0.1.2.zip'
files = {f'app/{p.name}': p for p in sorted((root / 'app').glob('*.py'))}
files.update({
    'install.sh': root / 'distribution/install.sh',
    'production.env.example': root / 'distribution/production.env.example',
    'README.md': root / 'distribution/README.md',
    'LICENSE': root / 'LICENSE',
    'requirements.txt': root / 'requirements.txt',
})
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for name, path in sorted(files.items()):
        info = zipfile.ZipInfo('snaptrade-pi-diy/' + name, (2026, 9, 14, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, path.read_bytes())
checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
(archive.with_suffix('.zip.sha256')).write_text(f'{checksum}  {archive.name}\n')
print(f'{archive.name}: {len(files)} files; SHA-256 {checksum}')
