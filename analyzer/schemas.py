from pydantic import BaseModel
from typing import List

class MetricResponse(BaseModel):
    descripcion: str
    valores: str

class DailyRecord(BaseModel):
    date: str
    docs_count: int
    total_keyword_hits: int
    colcap_close: float

class DailyResponse(BaseModel):
    descripcion: str
    data: List[DailyRecord]

class HealthResponse(BaseModel):
    status: str
    processor: str
    analyzer: str
    api: str

class PlotsResponse(BaseModel):
    descripcion: str
    plots: List[str]
