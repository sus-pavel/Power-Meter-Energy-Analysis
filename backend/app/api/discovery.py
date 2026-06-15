from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import CurrentUser, Database, require_permission
from backend.app.models.user import User
from backend.app.schemas.discovery import (
    ScanCancelResponse,
    ScanCreateRequest,
    ScanCreateResponse,
    ScanJobRead,
    ScanResultRead,
)
from backend.app.services import discovery_service
from backend.app.services.audit_service import write_audit_log
from backend.app.services.discovery_service import discovery_runtime


router = APIRouter(prefix="/api/discovery", tags=["discovery"])


def _job_response(job: discovery_service.ScanJob) -> ScanJobRead:
    return ScanJobRead(
        **job.__dict__,
        progress_percent=discovery_service.progress_percent(job),
    )


@router.post("/scan", response_model=ScanCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    payload: ScanCreateRequest,
    conn: Database,
    current_user: User = Depends(require_permission("scan_network")),
) -> ScanCreateResponse:
    job = discovery_service.create_scan_job(conn, payload, current_user.id)
    write_audit_log(
        conn,
        user_id=current_user.id,
        action="scan_created",
        entity_type="scan_job",
        entity_id=job.id,
        details={"ip_start": job.ip_start, "ip_end": job.ip_end, "total_hosts": job.total_hosts},
    )
    conn.commit()
    discovery_runtime.start(job.id, current_user.id)
    return ScanCreateResponse(job_id=job.id, status=job.status)


@router.get("/jobs", response_model=list[ScanJobRead])
def list_jobs(
    conn: Database,
    _: User = Depends(require_permission("view_discovery")),
) -> list[ScanJobRead]:
    return [_job_response(job) for job in discovery_service.list_scan_jobs(conn)]


@router.get("/jobs/{job_id}", response_model=ScanJobRead)
def get_job(
    job_id: int,
    conn: Database,
    _: User = Depends(require_permission("view_discovery")),
) -> ScanJobRead:
    job = discovery_service.get_scan_job(conn, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    return _job_response(job)


@router.get("/jobs/{job_id}/results", response_model=list[ScanResultRead])
def get_job_results(
    job_id: int,
    conn: Database,
    _: User = Depends(require_permission("view_discovery")),
) -> list[ScanResultRead]:
    if discovery_service.get_scan_job(conn, job_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    return [ScanResultRead(**result.__dict__) for result in discovery_service.list_scan_results(conn, job_id)]


@router.post("/jobs/{job_id}/cancel", response_model=ScanCancelResponse)
def cancel_job(
    job_id: int,
    conn: Database,
    current_user: User = Depends(require_permission("scan_network")),
) -> ScanCancelResponse:
    job = discovery_service.mark_job_cancelled(conn, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    discovery_runtime.cancel(job_id)
    write_audit_log(
        conn,
        user_id=current_user.id,
        action="scan_cancelled",
        entity_type="scan_job",
        entity_id=job_id,
        details={"status": job.status},
    )
    conn.commit()
    return ScanCancelResponse(job_id=job_id, status="cancelled", message="Scan cancellation requested.")
