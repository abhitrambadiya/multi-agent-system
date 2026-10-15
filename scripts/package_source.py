"""Source-only submission bundle: no secrets, model weights, raw data or environments."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
output=ROOT/'output/AI-EOS_Source.zip'
output.parent.mkdir(parents=True,exist_ok=True)
files=[]
for folder in ['backend','frontend/src','scripts','tests','eval','docs','results/benchmark','results/offline','results/ui','results/test-20261014T124545Z/code_snapshot']:
 for path in (ROOT/folder).rglob('*'):
  if path.is_file() and path.suffix in {'.py','.ts','.tsx','.css','.json','.jsonl','.md','.csv','.png','.jpg','.pdf','.sh','.txt'} and '__pycache__' not in path.parts:files.append(path)
for name in ['README.md','TASKS.md','.gitignore','pytest.ini','requirements.lock.txt','frontend/package.json','frontend/package-lock.json','frontend/tsconfig.json','frontend/tsconfig.node.json','frontend/vite.config.ts','frontend/tailwind.config.js','frontend/postcss.config.js','frontend/index.html','data/processed/manifest.json','data/model-manifest.json','results/calibration.json','results/startup/timings.json','results/test-build.log','output/AI-EOS_Implementation_Plan.md','output/pdf/AI-EOS_Implementation_Plan.pdf']:
 path=ROOT/name
 if path.exists():files.append(path)
with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for path in sorted(set(files)):z.write(path,path.relative_to(ROOT))
with zipfile.ZipFile(output) as z:
 assert z.testzip() is None
 assert not any('/node_modules/' in x or '/.env' in x or '/models/' in x for x in z.namelist())
print(f'{output}: {output.stat().st_size:,} bytes, {len(files)} files')
