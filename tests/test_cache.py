import numpy as np
import pytest
from backend.cache import AnswerCache
from backend.contracts import Request

class SameEmbedding:
 def encode(self,texts):return np.array([[1.,0.] for _ in texts])

def test_semantic_hit_matching_scope(store):
 c=AnswerCache(store,SameEmbedding());c.put('policy question',{'topic':'returns'},{'v':1},{'answer':'30 days'});r,info=c.lookup('paraphrase',{'topic':'returns'},{'v':1},'A3');assert r['answer']=='30 days';assert info['reason']=='semantic'
@pytest.mark.parametrize('key,value',[('category','other'),('period','2018-07'),('metric','orders'),('negation',True),('workspace','other'),('permissions','other'),('qualifiers',['damaged'])])
def test_critical_slots_never_ignored(store,key,value):
 c=AnswerCache(store,SameEmbedding());scope={'category':'one','period':'2018-06','metric':'sales','negation':False,'workspace':'local','permissions':'owner','qualifiers':[]};c.put('original',scope,{'v':1},{'answer':'old'});assert c.lookup('similar',{**scope,key:value},{'v':1},'A3')[0] is None
@pytest.mark.parametrize('key,value',[('business',2),('model','other'),('digest','new'),('dataset','new'),('prompt','v2'),('mode','TEMPLATE')])
def test_source_versions_never_ignored(store,key,value):
 c=AnswerCache(store,SameEmbedding());snapshot={'business':1,'model':'qwen','digest':'old','dataset':'old','prompt':'v1','mode':'LOCAL_LLM'};c.put('original',{},snapshot,{'answer':'old'});assert c.lookup('similar',{},dict(snapshot,**{key:value}),'A3')[0] is None

def test_unsafe_baseline_exposes_stale_reuse(store):
 c=AnswerCache(store,SameEmbedding());c.put('original',{'category':'one'},{'v':1},{'answer':'old'});assert c.lookup('similar',{'category':'other'},{'v':2},'A2')[0]['answer']=='old'
def test_exact_arm_rejects_paraphrase(store):
 c=AnswerCache(store,SameEmbedding());c.put('original',{},1,{'a':1});assert c.lookup('paraphrase',{},1,'A1')[0] is None

def test_semantic_qualifiers(engine):
 a=engine.resolve(Request(question='What is our return policy?').model_dump());b=engine.resolve(Request(question='What is our return policy for damaged goods?').model_dump());assert a!=b
