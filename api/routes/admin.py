"""Admin routes: vacuum job management."""
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from agents.RAG.vacuum import create_vacuum_job, run_vacuum_job, get_vacuum_job_status

router = APIRouter()


@router.post("/vacuum", status_code=202)
async def trigger_vacuum(background_tasks: BackgroundTasks):
    job_id = create_vacuum_job()
    background_tasks.add_task(run_vacuum_job, job_id)
    return {"job_id": str(job_id), "status": "pending"}


@router.get("/vacuum/status/{job_id}")
async def get_vacuum_status(job_id: uuid.UUID):
    status = get_vacuum_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Vacuum job not found")
    return status
