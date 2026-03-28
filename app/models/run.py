from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base

class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    requirement = Column(Text, nullable=True)  # Original requirement text
    status = Column(SQLEnum(RunStatus), default=RunStatus.PENDING)
    current_stage = Column(String, default="Requirement")
    checkpoint_id = Column(String, nullable=True)  # For LangGraph pause/resume
    selected_epic_id = Column(Integer, nullable=True)  # For story generation
    selected_story_id = Column(Integer, nullable=True)  # For spec generation
    user_feedback = Column(Text, nullable=True)  # For regeneration with feedback
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="runs")
    artifacts = relationship("Artifact", back_populates="run")
