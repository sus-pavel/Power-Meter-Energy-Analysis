from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import Database, require_permission
from backend.app.models.user import User
from backend.app.schemas.candidate import (
    CandidateDetails,
    CandidateProbeResponse,
    CandidatePromoteRequest,
    CandidatePromoteResponse,
    CandidateRejectResponse,
    CandidateSummary,
)
from backend.app.services import candidate_service
from backend.app.services.audit_service import write_audit_log
from backend.app.services.fingerprint_service import fingerprint_candidate
from backend.app.services.register_probe_service import probe_candidate


router = APIRouter(prefix="/api/candidates", tags=["candidates"])


def _summary(candidate) -> CandidateSummary:
    return CandidateSummary(
        id=candidate.id,
        ip_address=candidate.ip_address,
        port=candidate.port,
        unit_id=candidate.unit_id,
        status=candidate.status,
        device_type_guess=candidate.device_type_guess,
        confidence_score=candidate.confidence_score,
        vendor_guess=candidate.vendor_guess,
        vendor_name=candidate.vendor_name,
        product_code=candidate.product_code,
        product_name=candidate.product_name,
        model_name=candidate.model_name,
        firmware_revision=candidate.firmware_revision,
        vendor_identification_supported=candidate.vendor_identification_supported,
        vendor_identification_error=candidate.vendor_identification_error,
        probe_profile_id=candidate.probe_profile_id,
        probe_profile_source=candidate.probe_profile_source,
        probe_quality=candidate.probe_quality,
        probe_status=candidate.probe_status,
        updated_at=candidate.updated_at,
    )


@router.get("", response_model=list[CandidateSummary])
def list_candidates(
    conn: Database,
    _: User = Depends(require_permission("view_candidates")),
) -> list[CandidateSummary]:
    return [_summary(candidate) for candidate in candidate_service.list_candidates(conn)]


@router.get("/{candidate_id}", response_model=CandidateDetails)
def get_candidate(
    candidate_id: int,
    conn: Database,
    _: User = Depends(require_permission("view_candidates")),
) -> CandidateDetails:
    candidate = candidate_service.get_candidate(conn, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    probe_results = candidate_service.list_probe_results(conn, candidate_id)
    return CandidateDetails(
        **_summary(candidate).model_dump(),
        scan_result_id=candidate.scan_result_id,
        notes=candidate.notes,
        created_at=candidate.created_at,
        device_identification_raw=candidate.device_identification_raw,
        probe_summary_json=candidate.probe_summary_json,
        probe_results=[result.__dict__ for result in probe_results],
    )


@router.post("/{candidate_id}/probe", response_model=CandidateProbeResponse)
async def probe(
    candidate_id: int,
    conn: Database,
    current_user: User = Depends(require_permission("manage_candidates")),
) -> CandidateProbeResponse:
    candidate = candidate_service.get_candidate(conn, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    if candidate.status in {"promoted", "rejected"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Candidate is closed")

    probe_outcome = await probe_candidate(candidate, conn)
    candidate_service.update_candidate_probe_metadata(conn, candidate_id, metadata=probe_outcome["metadata"])
    probe_results = candidate_service.replace_probe_results(conn, candidate_id, probe_outcome["results"])
    candidate = candidate_service.get_candidate(conn, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    fingerprint = fingerprint_candidate(candidate, probe_results)
    candidate_service.update_candidate_fingerprint(
        conn,
        candidate_id,
        device_type_guess=fingerprint.device_type_guess,
        confidence_score=fingerprint.confidence_score,
        vendor_guess=fingerprint.vendor_guess,
    )
    write_audit_log(
        conn,
        user_id=current_user.id,
        action="candidate_probed",
        entity_type="discovered_candidate",
        entity_id=candidate_id,
        details={
            "valid_registers_found": sum(1 for result in probe_results if result.valid),
            "device_type_guess": fingerprint.device_type_guess,
            "confidence_score": fingerprint.confidence_score,
            "probe_quality": candidate.probe_quality,
            "probe_profile_source": candidate.probe_profile_source,
        },
    )
    return CandidateProbeResponse(
        candidate_id=candidate_id,
        probe_status=candidate.probe_status or "completed",
        valid_registers_found=sum(1 for result in probe_results if result.valid),
        device_type_guess=fingerprint.device_type_guess,
        confidence_score=fingerprint.confidence_score,
        probe_quality=candidate.probe_quality or "unknown",
        probe_profile_source=candidate.probe_profile_source,
    )


@router.post("/{candidate_id}/promote", response_model=CandidatePromoteResponse)
def promote(
    candidate_id: int,
    payload: CandidatePromoteRequest,
    conn: Database,
    current_user: User = Depends(require_permission("manage_candidates")),
) -> CandidatePromoteResponse:
    candidate = candidate_service.get_candidate(conn, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    if candidate.status == "promoted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Candidate is already promoted")
    if candidate.status == "rejected":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Rejected candidate cannot be promoted")

    device_id, registers_created = candidate_service.promote_candidate(conn, candidate, payload)
    write_audit_log(
        conn,
        user_id=current_user.id,
        action="candidate_promoted",
        entity_type="discovered_candidate",
        entity_id=candidate_id,
        details={"candidate_id": candidate_id, "device_id": device_id, "registers_created": registers_created},
    )
    return CandidatePromoteResponse(
        candidate_id=candidate_id,
        device_id=device_id,
        status="promoted",
        registers_created=registers_created,
    )


@router.post("/{candidate_id}/reject", response_model=CandidateRejectResponse)
def reject(
    candidate_id: int,
    conn: Database,
    current_user: User = Depends(require_permission("manage_candidates")),
) -> CandidateRejectResponse:
    candidate = candidate_service.reject_candidate(conn, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    write_audit_log(
        conn,
        user_id=current_user.id,
        action="candidate_rejected",
        entity_type="discovered_candidate",
        entity_id=candidate_id,
        details={"candidate_id": candidate_id},
    )
    return CandidateRejectResponse(candidate_id=candidate_id, status="rejected", message="Candidate rejected.")
