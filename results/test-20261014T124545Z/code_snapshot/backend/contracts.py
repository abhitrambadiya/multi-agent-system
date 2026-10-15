from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class Request(BaseModel):
    model_config=ConfigDict(extra='forbid')
    question: str=Field(min_length=3,max_length=1000)
    kind: Literal['auto','policy','metrics','investigation','replenishment']='auto'
    category: str='furniture_decor'
    period_a: str='2018-05'
    period_b: str='2018-06'
    sku: Literal['DEMO-CHAIR']='DEMO-CHAIR'
    cache: Literal['A0','A1','A3']='A3'

class Decision(BaseModel):
    model_config=ConfigDict(extra='forbid')
    decision: Literal['APPROVE','REJECT']
    digest: str=Field(min_length=64,max_length=64)

class PolicyEdit(BaseModel):
    days: int=Field(ge=1,le=90)

class Summary(BaseModel):
    summary: str=Field(max_length=2200)
    citations: list[str]=Field(max_length=8)
    limitations: list[str]=Field(max_length=5)
