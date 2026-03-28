from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.artifact import Artifact
from app.models.run import Run
from app.models.user import User
from app.core.security import get_current_user
from app.services.export_service import ExportService
import io
import json

router = APIRouter()

@router.get("/{artifact_id}")
async def get_artifact(
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific artifact."""
    result = await db.execute(select(Artifact).filter(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    return artifact

@router.get("/{artifact_id}/export/pdf")
async def export_artifact_pdf(
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export artifact as PDF."""
    result = await db.execute(select(Artifact).filter(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    try:
        pdf_buffer = ExportService.create_pdf_report(
            title=f"{artifact.type} Artifact",
            artifacts=[{
                "type": artifact.type,
                "content": artifact.content
            }]
        )
        
        return StreamingResponse(
            io.BytesIO(pdf_buffer.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=artifact_{artifact_id}.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@router.get("/{artifact_id}/export/markdown")
async def export_artifact_markdown(
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export artifact as Markdown."""
    result = await db.execute(select(Artifact).filter(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    try:
        md_content = ExportService.format_markdown(artifact.type, artifact.content)
        
        return StreamingResponse(
            io.BytesIO(md_content.encode()),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=artifact_{artifact_id}.md"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Markdown export failed: {str(e)}")

@router.get("/{artifact_id}/export/code-zip")
async def export_code_zip(
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Artifact).filter(Artifact.id == artifact_id, Artifact.type == "Code")
    )
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Code artifact not found")

    try:
        content = artifact.content

        # If stored as JSON string in DB
        if isinstance(content, str):
            content = json.loads(content)

        if not isinstance(content, dict) or not content:
            raise HTTPException(status_code=400, detail="No code files found in artifact")

        zip_buffer = ExportService.create_code_bundle(content)

        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=generated_code_{artifact_id}.zip"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZIP export failed: {str(e)}")

@router.get("/run/{run_id}/export/full-report")
async def export_full_report(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export complete run report as ZIP with all artifacts."""
    result = await db.execute(select(Run).filter(Run.id == run_id))
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        # Get all artifacts for this run
        artifacts_result = await db.execute(
            select(Artifact).filter(Artifact.run_id == run_id).order_by(Artifact.created_at)
        )
        artifacts = artifacts_result.scalars().all()
        
        # Create full report
        zip_buffer = ExportService.create_full_report(
            run_data={"id": run.id, "project_id": run.project_id, "status": run.status.value},
            artifacts=[{
                "type": a.type,
                "content": a.content,
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in artifacts]
        )
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=run_report_{run_id}.zip"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report export failed: {str(e)}")

@router.get("/run/{run_id}/export/structured")
async def export_structured(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export artifacts in structured format: epics.md, stories.md, spec.md, validation_report.json, code.zip"""
    result = await db.execute(select(Run).filter(Run.id == run_id))
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        artifacts_result = await db.execute(
            select(Artifact).filter(Artifact.run_id == run_id).order_by(Artifact.created_at)
        )
        artifacts = artifacts_result.scalars().all()
        
        # Create structured ZIP
        import zipfile
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add each artifact type as specified files
            for artifact in artifacts:
                if artifact.type == "Epic":
                    md = ExportService.format_markdown("Epics", artifact.content)
                    zf.writestr("epics.md", md)
                
                elif artifact.type == "Story":
                    md = ExportService.format_markdown("User Stories", artifact.content)
                    zf.writestr("stories.md", md)
                
                elif artifact.type == "Spec":
                    md = ExportService.format_markdown("Technical Specification", artifact.content)
                    zf.writestr("spec.md", md)
                
                elif artifact.type == "Validation":
                    import json
                    zf.writestr("validation_report.json", json.dumps(artifact.content, indent=2))
                
                elif artifact.type == "Code":
                    files = artifact.content.get("files", {})
                    for file_path, content in files.items():
                        zf.writestr(f"generated_code/{file_path}", content)
            
            # Add metadata
            import json
            metadata = {
                "run_id": run.id,
                "project_id": run.project_id,
                "requirement": run.requirement,
                "status": run.status.value,
                "created_at": run.created_at.isoformat() if run.created_at else None
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=project_export_{run_id}.zip"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
