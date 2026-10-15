"""Frozen family-level split; answer metadata never enters application retrieval."""
import json,hashlib
from pathlib import Path
from backend.retrieval import POLICIES
from backend.analytics import Analytics
from backend.config import Settings
root=Path(__file__).resolve().parents[1]
categories=[x['category'] for x in Analytics(Settings().analytics).categories()][:16]
families=[]
for cls in ['policy','metrics','investigation']:
 for i in range(16):
  split='design' if i<8 else 'dev' if i<12 else 'test'
  if cls=='policy':
   topic=list(POLICIES)[i];start=0 if i<8 else 8 if i<12 else 12;size=8 if i<8 else 4;other=list(POLICIES)[start+(i-start+1)%size]
   base={'kind':'policy','question':f'What is our {topic} policy?'}
   requests=[base,base,{**base,'question':f'Please describe our {topic} policy.'},{**base,'question':f'What is our {other} policy?'},{**base,'question':f'What is not covered by our {topic} policy?'}]
   gold=[{'topic':topic,'negation':False}]*3+[{'topic':other,'negation':False},{'topic':topic,'negation':True}]
  else:
   cat=categories[i];start=0 if i<8 else 8 if i<12 else 12;size=8 if i<8 else 4;other=categories[start+(i-start+1)%size]
   verb='Compare' if cls=='metrics' else 'Investigate'
   base={'kind':cls,'question':f'{verb} sales for {cat}.','category':cat,'period_a':'2018-06','period_b':'2018-07'}
   requests=[base,base,{**base,'question':f'Please {verb.lower()} historical sales for {cat}.'},{**base,'question':f'{verb} sales for {other}.','category':other},{**base,'period_a':'2018-05'}]
   gold=[{'category':cat,'period_a':'2018-06','period_b':'2018-07'}]*3+[{'category':other,'period_a':'2018-06','period_b':'2018-07'},{'category':cat,'period_a':'2018-05','period_b':'2018-07'}]
  families.append({'id':f'{cls}-{i:02d}','class':cls,'split':split,'requests':[{'index':j,'request':r,'expected_scope':g,'relation':['seed','identical','equivalent','near-miss','near-miss'][j]} for j,(r,g) in enumerate(zip(requests,gold))]})
content=json.dumps({'version':'v2-disjoint-splits','families':families,'note':'Synthetic question families over real Olist metrics and fictional policies. Family splits fixed before threshold calibration. Gold metadata is excluded from model prompts.'},indent=2)
(root/'eval/query_manifest.json').write_text(content)
print('families',len(families),'requests',sum(len(f['requests']) for f in families),'sha256',hashlib.sha256(content.encode()).hexdigest())
