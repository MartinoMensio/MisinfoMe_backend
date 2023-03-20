from fastapi import APIRouter, Path, Query

from ..model import jobs_manager

router = APIRouter()


@router.get('/status/{job_id}')
def get_job_status(job_id: str = Path(..., description='The job_id to get the status from')):
    """Get the statuses of the jobs"""
    return jobs_manager.get_task_status(job_id)


@router.get('/status_by_callback_url')
def get_job_status_from_callback_url(
    callback_url: str = Query(..., description='The callback_url that was sent from the gateway')):
    """Get the statuses of the job from the callback_url"""
    return jobs_manager.get_task_status_from_callback_url(callback_url)
