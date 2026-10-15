"""Real local inference validation; writes actual observations, never estimates."""
import json,time
from pathlib import Path
from backend.config import Settings,ROOT
from backend.engine import Engine
from backend.contracts import Request
out=ROOT/'results/model-smoke';out.mkdir(parents=True,exist_ok=True)
e=Engine(Settings(db=out/'smoke.sqlite'))
health=e.llm.health()
if not health['ready']:raise RuntimeError('Model not ready')
rows=[]
for kind,q in [('policy','What is our return policy?'),('investigation','Investigate the sales change and propose a plan.')]:
 wid=e.start(Request(question=q,kind=kind,cache='A0'));start=time.perf_counter();r=e.run(wid);rows.append(r)
 print(kind,r['status'],r['error'],round(time.perf_counter()-start,2),r['usage'],flush=True)
 if r['status']!='COMPLETED':raise RuntimeError(r['error'])
 print(r['result']['summary'],flush=True)
(out/'results.json').write_text(json.dumps({'health':health,'embedding':e.embedding_mode,'workflows':rows},indent=2,ensure_ascii=False));e.close()
