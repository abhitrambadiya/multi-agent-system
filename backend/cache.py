import json,re,time
import numpy as np
from .db import dumps,uid

def normalize(q): return ' '.join(re.findall(r'\w+',q.casefold()))

class AnswerCache:
    def __init__(self,store,embedder,threshold=.82): self.store,self.embedder,self.threshold=store,embedder,threshold
    def lookup(self,q,scope,snapshot,arm):
        if arm=='A0': return None,{'hit':False,'reason':'disabled'}
        rows=self.store.rows('SELECT * FROM cache ORDER BY created DESC LIMIT 500')
        vec=self.embedder.encode([q])[0]
        reason='no equivalent candidate'
        for row in rows:
            exact=normalize(q)==normalize(row['query'])
            similarity=float(vec@np.array(json.loads(row['vector'])))
            if arm=='A1' and not exact: continue
            if not exact and similarity<self.threshold: continue
            if arm!='A2' and (row['scope']!=dumps(scope) or row['snapshot']!=dumps(snapshot)):
                reason='scope or source version changed'; continue
            result=json.loads(row['result'])
            return result,{'hit':True,'reason':'exact' if exact else 'semantic','similarity':round(similarity,4),'source_cache_id':row['id']}
        return None,{'hit':False,'reason':reason}
    def put(self,q,scope,snapshot,result):
        self.store.execute('INSERT INTO cache VALUES(?,?,?,?,?,?,?)',(uid(),q,dumps(self.embedder.encode([q])[0].tolist()),dumps(scope),dumps(snapshot),dumps(result),time.time()))
