"""Run A0-A3 in separate persistent sandboxes; no financial execution."""
import argparse,json,time,statistics,csv,hashlib,datetime
from pathlib import Path
from backend.config import Settings,ROOT
from backend.engine import Engine
from backend.contracts import Request
from backend.retrieval import Embedder


def main():
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['dev','test'],default='test');p.add_argument('--mode',choices=['TEMPLATE','LOCAL_LLM'],default='LOCAL_LLM');p.add_argument('--arms',default='A0,A1,A2,A3');p.add_argument('--limit-families',type=int);args=p.parse_args()
 manifest=json.loads((ROOT/'eval/query_manifest.json').read_text());families=[f for f in manifest['families'] if f['split']==args.split]
 if args.limit_families:families=families[:args.limit_families]
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');output=ROOT/'results'/f'{args.split}-{runid}';output.mkdir(parents=True)
 settings=Settings(mode=args.mode);embedder=Embedder(settings.models);allrows=[];arms=[]
 for arm in args.arms.split(','):
  if arm not in {'A0','A1','A2','A3'}:raise ValueError('Unknown arm')
  cfg=Settings(db=output/f'{arm}.sqlite',mode=args.mode);engine=Engine(cfg,embedder=embedder)
  health=engine.llm.health()
  if args.mode=='LOCAL_LLM' and not health['ready']:raise RuntimeError('Local model unavailable; benchmark cannot proceed')
  # Identical warmup per arm; excluded from request metrics, retained in ledger.
  if args.mode=='LOCAL_LLM':
   doc=engine.store.evidence('SIMULATED_POLICY','warmup','v1','All financial commitments require owner approval.')
   engine.llm.summarize('warmup','manager','Summarize the approval rule',[doc],doc['text'])
  engine.retriever.ensure('furniture_decor')
  for family in families:
   for case in family['requests']:
    req=Request(**case['request']);wid=engine.start(req);start=time.perf_counter();r=engine.run(wid,arm=arm);elapsed=(time.perf_counter()-start)*1000
    result=r.get('result') or {};scope=result.get('scope',{});hit=result.get('cache',{}).get('hit',False)
    mismatch=any(scope.get(k)!=v for k,v in case['expected_scope'].items())
    row={'arm':arm,'family':family['id'],'index':case['index'],'relation':case['relation'],'workflow_id':wid,'request':case['request'],'expected_scope':case['expected_scope'],'served_scope':scope,'status':r['status'],'error':r['error'],'hit':hit,'incorrect_hit':bool(hit and mismatch),'scope_correct':not mismatch and r['status']=='COMPLETED','tokens':r['usage']['input_tokens']+r['usage']['output_tokens'],'calls':r['usage']['calls'],'elapsed_ms':elapsed,'cache':result.get('cache',{}),'summary':result.get('summary'),'verified_facts':result.get('verified_facts'),'snapshot':result.get('snapshot')}
    allrows.append(row)
    with (output/'requests.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(f'{arm} {family["id"]}/{case["index"]} {r["status"]} hit={hit} scope_error={mismatch} tokens={row["tokens"]} {elapsed/1000:.2f}s',flush=True)
  engine.close()
  rows=[r for r in allrows if r['arm']==arm];lat=sorted(r['elapsed_ms'] for r in rows);hits=sum(r['hit'] for r in rows);incorrect=sum(r['incorrect_hit'] for r in rows)
  arms.append({'arm':arm,'requests':len(rows),'tokens':sum(r['tokens'] for r in rows),'calls':sum(r['calls'] for r in rows),'hits':hits,'incorrect_hits':incorrect,'scope_hit_precision':(hits-incorrect)/hits if hits else None,'failures':sum(r['status']!='COMPLETED' for r in rows),'p50_ms':statistics.median(lat),'p95_ms':lat[min(len(lat)-1,int(.95*len(lat)))],'scope_accuracy':sum(r['scope_correct'] for r in rows)/len(rows)})
  (output/'summary.json').write_text(json.dumps({'run_id':runid,'model':settings.model,'model_digest':health.get('digest'),'mode':args.mode,'split':args.split,'arms':arms,'manifest_sha256':hashlib.sha256((ROOT/'eval/query_manifest.json').read_bytes()).hexdigest(),'threshold':settings.threshold,'note':'One paired pass. Incorrect hits mean oracle scope mismatch, not independent human scoring of generated prose. Gold labels excluded from prompts. Small synthetic query sample; no universal reliability claim.'},indent=2))
 with (output/'summary.csv').open('w') as f:
  writer=csv.DictWriter(f,fieldnames=list(arms[0]));writer.writeheader();writer.writerows(arms)
 if args.split=='test' and not args.limit_families and len(arms)==4 and args.mode=='LOCAL_LLM':
  dest=ROOT/'results/benchmark';dest.mkdir(exist_ok=True)
  (dest/'summary.json').write_text((output/'summary.json').read_text())
  (dest/'run_path.txt').write_text(str(output))
 print(output)

if __name__=='__main__':main()
