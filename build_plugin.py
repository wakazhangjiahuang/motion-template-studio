"""Build one private plugin archive from this repository's source Skill."""
from pathlib import Path
import tempfile,shutil,zipfile,sys
R=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R/'motion-template-studio-plugin.zip'
if out.exists():raise SystemExit('Refusing existing archive')
with tempfile.TemporaryDirectory(prefix='motion-plugin-') as td:
 root=Path(td)/'motion-template-studio';root.mkdir()
 shutil.copyfile(R/'plugin/plugin.json',root/'plugin.json')
 shutil.copytree(R/'skills/motion-template-studio',root/'skills/motion-template-studio',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(root.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(root.parent))
print(out)
