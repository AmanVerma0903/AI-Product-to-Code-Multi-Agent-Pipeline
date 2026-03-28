from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class ArtifactType(String):
    pass # Simple wrapper for readability in code

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    type = Column(String, nullable=False) # Research, Epic, Story, Spec, Code, Validation
    artifact_subtype = Column(String, nullable=True)  # For Mermaid diagrams: "mermaid_epic_diagram", etc.
    content = Column(JSON, nullable=False) # Structured data or file paths
    file_path = Column(String, nullable=True)  # For exported files (PDF, ZIP)
    storage_location = Column(String, nullable=True)  # URL for file download
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("Run", back_populates="artifacts")
