import pytest
from backend.db import Store
from backend.config import Settings
from backend.engine import Engine
from backend.retrieval import LexicalEmbedder

@pytest.fixture
def store(tmp_path):return Store(tmp_path/'test.sqlite')
@pytest.fixture
def engine(tmp_path):
    e=Engine(Settings(db=tmp_path/'app.sqlite',mode='TEMPLATE'),embedder=LexicalEmbedder())
    yield e
    e.close()
