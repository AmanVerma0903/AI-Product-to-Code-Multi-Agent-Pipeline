from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.project import Document
from app.models.vector_store import DocumentChunk
from openai import AsyncOpenAI


class RAGService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def index_document_chunks(self, document_id: int, content: str) -> int:
        chunks = self.chunk_text(content)
        for chunk in chunks:
            embedding = await self.get_embedding(chunk)
            self.db.add(
                DocumentChunk(
                    document_id=document_id,
                    content=chunk,
                    embedding=embedding,
                )
            )
        await self.db.commit()
        return len(chunks)

    def chunk_text(self, text: str, size: int = 1000) -> List[str]:
        return [text[i : i + size] for i in range(0, len(text), size)]

    async def get_embedding(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small",
        )
        return response.data[0].embedding

    async def search(self, project_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_embedding = await self.get_embedding(query)
        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(DocumentChunk, distance_expr.label("distance"))
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.project_id == project_id)
            .order_by(distance_expr)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        out: List[Dict[str, Any]] = []
        for row in rows:
            chunk = row[0]
            dist = row[1]
            out.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "distance": float(dist) if dist is not None else None,
                }
            )
        return out
