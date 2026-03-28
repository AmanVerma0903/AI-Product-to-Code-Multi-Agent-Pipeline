from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.run import RunStatus

class RunBase(BaseModel):
    project_id: int

class RunCreate(RunBase):
    requirement: str

class RunResponse(RunBase):
    id: int
    status: RunStatus
    current_stage: str
    created_at: datetime
    requirement: str

    class Config:
        from_attributes = True

class SpecApproval(BaseModel):
    approved: bool
    feedback: Optional[str] = None

class SpecGenerateRequest(BaseModel):
    story_id: int

class SpecReviewRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None

class SpecRegenerateRequest(BaseModel):
    feedback: str

class ValidateAndFixRequest(BaseModel):
    max_iterations: int = 3

class ArtifactResponse(BaseModel):
    id: int
    run_id: int
    type: str
    artifact_subtype: Optional[str] = None
    content: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
