from pathlib import Path
from huggingface_hub import snapshot_download
import json
root=Path(__file__).resolve().parents[1]
path=snapshot_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',local_dir=root/'data/models/minilm',allow_patterns=['*.json','*.safetensors','tokenizer*','sentencepiece*','*.model','modules.json','1_Pooling/*'],max_workers=4)
print(path)
