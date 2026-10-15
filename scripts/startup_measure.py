import time,json
from backend.config import ROOT,Settings
out=ROOT/'results/startup';out.mkdir(exist_ok=True)
start=time.perf_counter()
from backend.retrieval import Embedder
imported=time.perf_counter()
embedder=Embedder(Settings().models)
loaded=time.perf_counter()
from backend.db import Store
from backend.analytics import Analytics
from backend.retrieval import Retriever
retriever=Retriever(Store(out/'startup.sqlite'),Analytics(Settings().analytics),embedder)
retriever.ensure('furniture_decor')
indexed=time.perf_counter()
result={'embedding_module_import_ms':(imported-start)*1000,'embedding_constructor_ms':(loaded-imported)*1000,'initial_corpus_and_index_ms':(indexed-loaded)*1000,'documents':len(retriever.docs),'note':'Separate startup measurement in a fresh Python process with already downloaded files and potentially warm OS file cache; excludes Ollama model load. Benchmark invocation ledgers record generation load time separately.'}
(out/'timings.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
