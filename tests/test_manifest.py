import json
from pathlib import Path

def test_family_splits_and_counts():
 m=json.loads(Path('eval/query_manifest.json').read_text());families=m['families'];assert len(families)==48;assert len({f['id'] for f in families})==48
 assert {s:sum(f['split']==s for f in families) for s in ['design','dev','test']}=={'design':24,'dev':12,'test':12}
 assert all(len(f['requests'])==5 for f in families)
 assert all(f['requests'][0]['request']==f['requests'][1]['request'] for f in families)
 assert all(f['requests'][0]['expected_scope']==f['requests'][2]['expected_scope'] for f in families)
 assert all(f['requests'][0]['expected_scope']!=f['requests'][j]['expected_scope'] for f in families for j in [3,4])

def test_no_identical_request_leaks_across_splits():
 m=json.loads(Path('eval/query_manifest.json').read_text());seen={}
 for family in m['families']:
  for case in family['requests']:
   key=json.dumps(case['request'],sort_keys=True)
   if key in seen:assert seen[key]==family['split']
   seen[key]=family['split']
