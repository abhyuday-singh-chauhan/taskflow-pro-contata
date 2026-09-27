from pydantic import BaseModel
from typing import Optional


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "backlog"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    position: int = 0

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    position: Optional[int] = None

class DependencyCreate(BaseModel):
        depends_on_task_id: int

class AISuggestionRequest(BaseModel):
    title: str
    description: Optional[str] = None