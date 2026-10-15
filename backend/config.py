from pathlib import Path
from dataclasses import dataclass
import os

ROOT = Path(__file__).resolve().parents[1]

@dataclass
class Settings:
    db: Path = ROOT / 'data/runtime/aieos.sqlite'
    analytics: Path = ROOT / 'data/processed/olist.sqlite'
    models: Path = ROOT / 'data/models/minilm'
    mode: str = 'LOCAL_LLM'
    model: str = 'qwen3:4b'
    ollama: str = 'http://127.0.0.1:11434'
    timeout: float = 120
    threshold: float = .82
    token_limit: int = 16000

    @classmethod
    def env(cls):
        s = cls()
        s.db = Path(os.getenv('AIEOS_DB', str(s.db)))
        s.mode = os.getenv('AIEOS_MODE', s.mode)
        if s.mode not in {'LOCAL_LLM', 'TEMPLATE'}:
            raise ValueError('AIEOS_MODE must be LOCAL_LLM or TEMPLATE')
        s.model = os.getenv('AIEOS_MODEL', s.model)
        return s
