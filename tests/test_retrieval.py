from backend.retrieval import POLICIES

def test_policy_retrieval_resolves_and_versions(engine):
 for topic in POLICIES:
  docs=engine.retriever.search(f'What is our {topic} policy?','furniture_decor',topic)
  assert docs[0]['locator']==f'policy/{topic}'
  assert len(docs)<=4
  assert sum(len(d['text']) for d in docs)<=3600
  assert all(engine.store.one('SELECT id FROM evidence WHERE id=?',(d['id'],)) for d in docs)
 old=engine.retriever.search('returns','furniture_decor','returns')[0]
 engine.store.update_policy(14)
 new=engine.retriever.search('returns','furniture_decor','returns')[0]
 assert old['id']!=new['id'];assert '14 days' in new['text'];assert '30 days' in old['text']
