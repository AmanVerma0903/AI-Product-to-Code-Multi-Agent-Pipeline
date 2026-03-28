from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

from app.core.config import settings
from app.api.v1 import projects, runs, users, artifacts, rag, admin
from app.core.logging import setup_logging
from app.core.ws_manager import ws_manager
from sqlalchemy import text

from app.db.session import Base, async_engine

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Software Factory for transforming requirements into production code.",
    version="1.0.0",
)


@app.on_event("startup")
async def startup():
    import app.models.base  # noqa: F401 — register models on Base.metadata

    async with async_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/progress/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: int):
    await ws_manager.connect(run_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            response = await ws_manager.handle_message(run_id, message)
            if response:
                await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        ws_manager.disconnect(run_id, websocket)

app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(runs.router, prefix="/api/v1/runs", tags=["Runs"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["Artifacts"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

@app.get("/")
def root():
    return {"message": "Welcome to the AI Product-to-Code Platform"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)