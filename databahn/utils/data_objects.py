from pydantic import BaseModel
from typing import Optional, List


class ContentObject(BaseModel):
    text: Optional[str] = ""

class Result(BaseModel):
    content: Optional[List[ContentObject]] = []