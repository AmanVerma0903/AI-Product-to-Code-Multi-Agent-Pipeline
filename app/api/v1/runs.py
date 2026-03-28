from fastapi import APIRouter, Depends, HTTPException
 
from sqlalchemy import select
from app.db.session import get_db, AsyncSessionLocal
from app.models.run import Run, RunStatus
from app.models.artifact import Artifact
from app.schemas.run import RunCreate, RunResponse, ValidateAndFixRequest
from app.core.security import get_current_user
from app.workflows.orchestrator import execute_workflow
from app.agents.validation_agent import ValidationAgent
from app.core.ws_manager import ws_manager
import json
import asyncio

router = APIRouter()

# =====================================================
# CREATE RUN
# =====================================================

@router.post("/", response_model=RunResponse)
async def create_run(run_data: RunCreate,
                     current_user=Depends(get_current_user),
                     db=Depends(get_db)):

    db_run = Run(
        project_id=run_data.project_id,
        requirement=run_data.requirement,
        status=RunStatus.RUNNING,
        current_stage="Research"
    )

    db.add(db_run)
    await db.commit()
    await db.refresh(db_run)

    # Run workflow in true async task (fixes MissingGreenlet)
    asyncio.create_task(
        execute_workflow(
            run_id=db_run.id,
            requirement=db_run.requirement
        )
    )

    return db_run


# =====================================================
# GET RUN
# =====================================================

@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: int,
                  current_user=Depends(get_current_user),
                  db = Depends(get_db)):

    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# =====================================================
# PAUSE / RESUME
# =====================================================

@router.post("/{run_id}/pause")
async def pause_run(run_id: int,
                    current_user=Depends(get_current_user),
                    db  = Depends(get_db)):

    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    run.status = RunStatus.PAUSED
    await db.commit()

    ws_manager.run_states[run_id] = "paused"

    await ws_manager.broadcast_to_run(run_id, json.dumps({
        "stage": run.current_stage,
        "status": "paused"
    }))

    return {"status": "paused"}


@router.post("/{run_id}/resume")
async def resume_run(run_id: int,
                     current_user=Depends(get_current_user),
                     db= Depends(get_db)):

    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    run.status = RunStatus.RUNNING
    await db.commit()

    ws_manager.run_states[run_id] = "running"

    await ws_manager.broadcast_to_run(run_id, json.dumps({
        "stage": run.current_stage,
        "status": "resumed"
    }))

    return {"status": "resumed"}


# =====================================================
# VALIDATION API
# =====================================================

@router.post("/{run_id}/validate-and-fix")
async def validate_and_fix(run_id: int,
                           request: ValidateAndFixRequest,
                           current_user=Depends(get_current_user),
                           db = Depends(get_db)):

    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    # Run validation in async task (fixes greenlet crash)
    asyncio.create_task(
        execute_validation_with_auto_fix(
            run_id=run_id,
            max_iterations=request.max_iterations
        )
    )

    return {"status": "validation_started"}


# =====================================================
# BACKGROUND VALIDATION LOOP
# =====================================================

async def execute_validation_with_auto_fix(run_id: int, max_iterations: int = 3):

    iteration = 0

    while iteration < max_iterations:

        while ws_manager.is_paused(run_id):
            await asyncio.sleep(1)

        async with AsyncSessionLocal() as db:

            code_artifact = (await db.execute(
                select(Artifact)
                .filter(Artifact.run_id == run_id, Artifact.type == "Code")
                .order_by(Artifact.created_at.desc())
                .limit(1)
            )).scalar_one_or_none()

            if not code_artifact:
                return

            validation_agent = ValidationAgent()
            content = code_artifact.content or {}
            if not isinstance(content, dict):
                return
            files = content.get("files")
            if not files:
                return
            report = await validation_agent.run(files)

            db.add(Artifact(run_id=run_id, type="Validation", content=report))
            await db.commit()

            await ws_manager.broadcast_to_run(run_id, json.dumps({
                "stage": "validation",
                "status": report["status"],
                "iteration": iteration + 1
            }))

            if report["status"] == "passed":
                run = await db.get(Run, run_id)
                run.status = RunStatus.COMPLETED
                await db.commit()
                return

        iteration += 1