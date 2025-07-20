from pydantic import BaseModel
from typing import List

class AnalyseResponse(BaseModel):
    message: str
    clauses_detectees: List[str]
