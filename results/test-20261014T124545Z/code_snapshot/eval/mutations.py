import json,time,datetime
from backend.config import ROOT,Settings
from backend.engine import Engine
from backend.contracts import Request
from backend.retrieval import Embedder
out=ROOT/'results'/('mutations-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir(parents=True)
embedder=Embedder(Settings().models);rows=[]
for arm in ['A0','A1','A2','A3']:
 e=Engine(Settings(db=out/f'{arm}.sqlite'),embedder=embedder)
 for i,days in enumerate([30,14]):
  if i:e.store.update_policy(days)
  w=e.start(Request(question='What is our return policy?',kind='policy'));r=e.run(w,arm=arm)
  result=r.get('result') or {};stale=f'{days} days' not in result.get('verified_facts','')
  rows.append({'arm':arm,'expected_days':days,'status':r['status'],'hit':result.get('cache',{}).get('hit',False),'stale':stale,'summary':result.get('summary'),'verified_facts':result.get('verified_facts'),'usage':r['usage']})
  print(arm,days,r['status'],'stale=',stale,flush=True)
 e.close()
(out/'results.json').write_text(json.dumps(rows,indent=2));print(out)
