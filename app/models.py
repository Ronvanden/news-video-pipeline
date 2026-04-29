from pydantic import BaseModel
from typing import List

class GenerateScriptRequest(BaseModel):
    url: str
    target_language: str = "de"
    duration_minutes: int = 10

class Chapter(BaseModel):
    title: str
    content: str

class GenerateScriptResponse(BaseModel):
    title: str
    hook: str
    chapters: List[Chapter]
    full_script: str
    sources: List[str]
    warnings: List[str]