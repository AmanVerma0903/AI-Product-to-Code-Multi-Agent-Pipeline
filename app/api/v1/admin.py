from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project
from app.models.run import Run, RunStatus
from app.core.security import get_admin_user
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/users")
async def get_all_users(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users in the system (admin only)."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    return {
        "total_users": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "is_active": u.is_active,
                "is_admin": u.is_admin
            }
            for u in users
        ]
    }

@router.get("/projects")
async def get_all_projects(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all projects in the system (admin only)."""
    result = await db.execute(select(Project))
    projects = result.scalars().all()
    
    return {
        "total_projects": len(projects),
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "owner_id": p.owner_id
            }
            for p in projects
        ]
    }

@router.get("/analytics")
async def get_analytics(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system analytics and statistics (admin only)."""
    
    # Count total users
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0
    
    # Count active users
    active_users_result = await db.execute(
        select(func.count(User.id)).filter(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0
    
    # Count admin users
    admin_result = await db.execute(
        select(func.count(User.id)).filter(User.is_admin == True)
    )
    admin_count = admin_result.scalar() or 0
    
    # Count total projects
    projects_result = await db.execute(select(func.count(Project.id)))
    total_projects = projects_result.scalar() or 0
    
    # Count total runs
    runs_result = await db.execute(select(func.count(Run.id)))
    total_runs = runs_result.scalar() or 0
    
    # Count runs by status
    completed_result = await db.execute(
        select(func.count(Run.id)).filter(Run.status == RunStatus.COMPLETED)
    )
    completed_runs = completed_result.scalar() or 0
    
    failed_result = await db.execute(
        select(func.count(Run.id)).filter(Run.status == RunStatus.FAILED)
    )
    failed_runs = failed_result.scalar() or 0
    
    running_result = await db.execute(
        select(func.count(Run.id)).filter(Run.status == RunStatus.RUNNING)
    )
    running_runs = running_result.scalar() or 0
    
    paused_result = await db.execute(
        select(func.count(Run.id)).filter(Run.status == RunStatus.PAUSED)
    )
    paused_runs = paused_result.scalar() or 0
    
    # Calculate success rate
    success_rate = 0.0
    if total_runs > 0:
        success_rate = (completed_runs / total_runs) * 100
    
    # Get recent run details
    recent_runs_result = await db.execute(
        select(Run).order_by(Run.created_at.desc()).limit(10)
    )
    recent_runs = recent_runs_result.scalars().all()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "users": {
            "total": total_users,
            "active": active_users,
            "admin": admin_count
        },
        "projects": {
            "total": total_projects
        },
        "runs": {
            "total": total_runs,
            "completed": completed_runs,
            "failed": failed_runs,
            "running": running_runs,
            "paused": paused_runs,
            "success_rate_percent": round(success_rate, 2)
        },
        "recent_runs": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "status": r.status.value,
                "current_stage": r.current_stage,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in recent_runs
        ]
    }

@router.get("/runs")
async def get_all_runs(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Get all runs in the system with status (admin only)."""
    result = await db.execute(
        select(Run).order_by(Run.created_at.desc()).limit(limit)
    )
    runs = result.scalars().all()
    
    return {
        "total_returned": len(runs),
        "runs": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "status": r.status.value,
                "current_stage": r.current_stage,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            }
            for r in runs
        ]
    }

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user and all their projects (admin only)."""
    user = await db.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_admin and user.id != admin_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another admin")
    
    try:
        # Delete user (cascade delete projects and runs)
        await db.delete(user)
        await db.commit()
        
        return {"status": "deleted", "user_id": user_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project and all its runs (admin only)."""
    project = await db.get(Project, project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Delete project (cascade delete runs)
        await db.delete(project)
        await db.commit()
        
        return {"status": "deleted", "project_id": project_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
