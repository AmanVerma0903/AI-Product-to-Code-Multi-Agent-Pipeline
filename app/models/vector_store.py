from sqlalchemy import Column, Integer, String, ForeignKey, Text
from pgvector.sqlalchemy import Vector
from app.db.session import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536)) # OpenAI embedding size
    metadata_json = Column(Text) # Additional context
