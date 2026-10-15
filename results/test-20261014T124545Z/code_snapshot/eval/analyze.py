"""Validate paired results and export transparent counts, uncertainty and errors."""
import json,csv,sqlite3,hashlib,shutil,statistics
from pathlib import Path
import numpy as np
from backend.config import ROOT
base=ROOT/'results/benchmark';run=Path((base/'run_path.txt').read_text())
if (run/'EXCLUDED.md').exists():raise RuntimeError('Excluded run cannot be reported')
rows=[json.loads(line) for line in (run/'requests.jsonl').read_text().splitlines()]
summary=json.loads((run/'summary.json').read_text())
assert len(rows)==240 and all(a['requests']==60 for a in summary['arms'])
keys={(r['family'],r['index']) for r in rows if r['arm']=='A0'}
assert len(keys)==60
for arm in ['A1','A2','A3']:assert {(r['family'],r['index']) for r in rows if r['arm']==arm}==keys
for arm in summary['arms']:
 with sqlite3.connect(run/f"{arm['arm']}.sqlite") as c:
  arm['failed_generation_attempts']=c.execute("SELECT COUNT(*) FROM invocations WHERE workflow_id!='warmup' AND status='FAILED'").fetchone()[0]
  arm['unknown_usage_attempts']=c.execute("SELECT COUNT(*) FROM invocations WHERE workflow_id!='warmup' AND (input_tokens IS NULL OR output_tokens IS NULL)").fetchone()[0]
  arm['mean_ms']=statistics.mean(r['elapsed_ms'] for r in rows if r['arm']==arm['arm'])
  for tokens, calls in c.execute("SELECT COALESCE(SUM(input_tokens+output_tokens),0),COUNT(*) FROM invocations WHERE workflow_id!='warmup'"):
   assert tokens==arm['tokens'] and calls==arm['calls']
a0=next(a for a in summary['arms'] if a['arm']=='A0');a3=next(a for a in summary['arms'] if a['arm']=='A3')
summary['a3_token_reduction_pct']=100*(1-a3['tokens']/a0['tokens'])
summary['a3_mean_latency_reduction_pct']=100*(1-a3['mean_ms']/a0['mean_ms'])
# Descriptive sensitivity to which task families were sampled; sequential cache makes families dependent.
families=sorted({r['family'] for r in rows});totals={a:[sum(r['tokens'] for r in rows if r['arm']==a and r['family']==f) for f in families] for a in ['A0','A3']}
rng=np.random.default_rng(42);draws=[]
for _ in range(5000):
 ids=rng.integers(0,len(families),len(families));b=sum(totals['A0'][i] for i in ids);o=sum(totals['A3'][i] for i in ids);draws.append(100*(1-o/b))
summary['token_reduction_family_resampling_95_percentile_range']=np.percentile(draws,[2.5,97.5]).tolist()
summary['uncertainty_note']='Descriptive family-resampling sensitivity range, not a confidence guarantee: sequential cache behavior makes family outcomes dependent. One pass, 12 held-out families, synthetic questions.'
summary['software']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['backend','eval'] for p in (ROOT/folder).glob('*.py')}
summary['dependencies_sha256']=hashlib.sha256((ROOT/'requirements.lock.txt').read_bytes()).hexdigest()
summary['dataset_sha256']=json.loads((ROOT/'data/processed/manifest.json').read_text())['archive_sha256']
summary['model_manifest']='data/model-manifest.json'
for target in [run/'summary.json',base/'summary.json']:target.write_text(json.dumps(summary,indent=2))
shutil.copy2(run/'requests.jsonl',base/'requests.jsonl')
shutil.copy2(ROOT/'eval/query_manifest.json',run/'query_manifest.json')
shutil.copy2(ROOT/'results/calibration.json',run/'calibration.json')
for folder in ['backend','eval']:
 dest=run/'code_snapshot'/folder;dest.mkdir(parents=True,exist_ok=True)
 for p in (ROOT/folder).glob('*.py'):shutil.copy2(p,dest/p.name)
with (base/'summary.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=list(summary['arms'][0]));writer.writeheader();writer.writerows(summary['arms'])
errors=[r for r in rows if r['incorrect_hit'] or r['status']!='COMPLETED']
(base/'error-cases.json').write_text(json.dumps(errors,indent=2,ensure_ascii=False))
text=['# Measured held-out results','',f"Run `{summary['run_id']}` · Qwen3:4b · LOCAL_LLM · one pass · 60 requests per arm.",'','| Arm | Tokens | Calls | Hits | Scope-mismatched hits | Failed requests | p50 seconds | p95 seconds |','|---|---:|---:|---:|---:|---:|---:|---:|']
for a in summary['arms']:text.append(f"| {a['arm']} | {a['tokens']:,} | {a['calls']} | {a['hits']} | {a['incorrect_hits']} | {a['failures']} | {a['p50_ms']/1000:.2f} | {a['p95_ms']/1000:.2f} |")
text+=['',f"A3 used **{summary['a3_token_reduction_pct']:.2f}% fewer measured generation tokens** than A0 on this trace. Mean request latency was {summary['a3_mean_latency_reduction_pct']:.2f}% lower.",'',f"Family-resampling sensitivity range for token reduction: {summary['token_reduction_family_resampling_95_percentile_range'][0]:.2f}%–{summary['token_reduction_family_resampling_95_percentile_range'][1]:.2f}%. {summary['uncertainty_note']}",'','Scope-mismatched hits compare returned task context with predeclared oracle fields. They do not measure every factual or linguistic error in generated prose. A2 is deliberately unsafe and is unavailable in the live API. No paid API costs or energy savings were measured. Failed/repair generation attempts count toward token totals; unknown usage is reported separately.','',f"Dataset SHA-256: `{summary['dataset_sha256']}`",f"Query manifest SHA-256: `{summary['manifest_sha256']}`",f"Model digest: `{summary['model_digest']}`",'','See `requests.jsonl`, `error-cases.json`, `summary.csv`, the run SQLite ledgers and `code_snapshot/` for reproduction.']
(base/'RESULTS.md').write_text('\n'.join(text)+'\n')
print('\n'.join(text[:14]))
