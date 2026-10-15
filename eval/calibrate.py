import json,time
import numpy as np
from backend.config import Settings,ROOT
from backend.engine import Engine
from backend.contracts import Request
from backend.retrieval import Embedder
s=Settings(db=ROOT/'tmp/calibration.sqlite',mode='TEMPLATE');e=Engine(s)
families=[f for f in json.loads((ROOT/'eval/query_manifest.json').read_text())['families'] if f['split']=='dev']
pairs=[]
for f in families:
 seed=f['requests'][0];a=Request(**seed['request']).model_dump();scope=e.resolve(a)
 for c in f['requests'][2:]:
  b=Request(**c['request']).model_dump();sim=float(e.embedder.encode([a['question']])[0]@e.embedder.encode([b['question']])[0]);same=scope==e.resolve(b)
  pairs.append({'family':f['id'],'relation':c['relation'],'similarity':sim,'scope_equal':same})
scores=[]
for t in [.75,.8,.82,.85,.9,.95]:
 hits=[r for r in pairs if r['scope_equal'] and r['similarity']>=t];scores.append({'threshold':t,'equivalent_hits':sum(r['relation']=='equivalent' for r in hits),'unsafe_hits':sum(r['relation']!='equivalent' for r in hits)})
# Predeclared conservative .82 retained if zero unsafe development hits; otherwise raise.
choice=next((r['threshold'] for r in scores if r['threshold']>=.82 and r['unsafe_hits']==0),None)
result={'split':'dev','pairs':pairs,'thresholds':scores,'chosen_threshold':choice,'note':'Calibrated on development families only. Scope checks precede reuse; embedding similarity is not an equivalence guarantee.'}
(ROOT/'results/calibration.json').write_text(json.dumps(result,indent=2));print(json.dumps(scores,indent=2));print('chosen',choice);e.close()
