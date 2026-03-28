from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel

class AgentState(TypedDict):
    project_id: int
    run_id: int
    requirement: str
    documents: List[str]
    research_summary: Optional[str]
    epics: Optional[List[Dict[str, Any]]]
    stories: Optional[List[Dict[str, Any]]]
    spec: Optional[Dict[str, Any]]
    code_files: Optional[Dict[str, str]]
    validation_report: Optional[Dict[str, Any]]
    current_stage: str
    approval_status: str # pending, approved, rejected
    user_feedback: Optional[str]
    mid_run_questions: Optional[List[str]]  # Q&A mid-run
    logs: List[str]

