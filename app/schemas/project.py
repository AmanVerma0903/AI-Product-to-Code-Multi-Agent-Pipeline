from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    

    class Config:
        from_attributes = True
        orm_mode = True # For Pydantic v1 compatibility if needed, but using v2
