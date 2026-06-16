from __future__ import annotations

import sqlite3
from typing import Optional

from backend.app.models.candidate import CandidateProbeResult, DiscoveredCandidate
from backend.app.schemas.candidate import CandidatePromoteRequest


def row_to_candidate(row: sqlite3.Row) -> DiscoveredCandidate:
    return DiscoveredCandidate(
        id=row["id"],
        scan_result_id=row["scan_result_id"],
        ip_address=row["ip_address"],
        port=row["port"],
        unit_id=row["unit_id"],
        status=row["status"],
        device_type_guess=row["device_type_guess"],
        confidence_score=row["confidence_score"],
        vendor_guess=row["vendor_guess"],
        vendor_name=row["vendor_name"],
        product_code=row["product_code"],
        product_name=row["product_name"],
        model_name=row["model_name"],
        firmware_revision=row["firmware_revision"],
        device_identification_raw=row["device_identification_raw"],
        vendor_identification_supported=bool(row["vendor_identification_supported"]),
        vendor_identification_error=row["vendor_identification_error"],
        probe_profile_id=row["probe_profile_id"],
        probe_profile_source=row["probe_profile_source"],
        probe_quality=row["probe_quality"],
        probe_status=row["probe_status"],
        probe_summary_json=row["probe_summary_json"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_probe_result(row: sqlite3.Row) -> CandidateProbeResult:
    return CandidateProbeResult(
        id=row["id"],
        candidate_id=row["candidate_id"],
        register_address=row["register_address"],
        function_code=row["function_code"],
        data_type=row["data_type"],
        raw_value=row["raw_value"],
        decoded_value=row["decoded_value"],
        valid=bool(row["valid"]),
        metric=row["metric"],
        scale=row["scale"],
        unit=row["unit"],
        quality=row["quality"],
        status=row["status"],
        source=row["source"],
        tested_json=row["tested_json"],
        inferred_json=row["inferred_json"],
        failure_reason=row["failure_reason"],
        exception_code=row["exception_code"],
        response_time_ms=row["response_time_ms"],
        validated_from_config=bool(row["validated_from_config"]),
        probe_profile_id=row["probe_profile_id"],
        probe_profile_source=row["probe_profile_source"],
        created_at=row["created_at"],
    )


def create_candidates_from_scan_result(
    conn: sqlite3.Connection,
    *,
    scan_result_id: int,
    ip_address: str,
    port: int,
    unit_ids: list[int],
) -> None:
    for unit_id in unit_ids:
        conn.execute(
            """
            INSERT OR IGNORE INTO discovered_candidates (
                scan_result_id, ip_address, port, unit_id, status, device_type_guess, confidence_score, vendor_guess
            )
            VALUES (?, ?, ?, ?, 'discovered', 'unknown_modbus_device', 0.2, 'unknown')
            """,
            (scan_result_id, ip_address, port, unit_id),
        )


def list_candidates(conn: sqlite3.Connection) -> list[DiscoveredCandidate]:
    rows = conn.execute("SELECT * FROM discovered_candidates ORDER BY updated_at DESC, id DESC").fetchall()
    return [row_to_candidate(row) for row in rows]


def get_candidate(conn: sqlite3.Connection, candidate_id: int) -> Optional[DiscoveredCandidate]:
    row = conn.execute("SELECT * FROM discovered_candidates WHERE id = ?", (candidate_id,)).fetchone()
    return row_to_candidate(row) if row else None


def list_probe_results(conn: sqlite3.Connection, candidate_id: int) -> list[CandidateProbeResult]:
    rows = conn.execute(
        """
        SELECT * FROM candidate_probe_results
        WHERE candidate_id = ?
        ORDER BY valid DESC, function_code, register_address, data_type
        """,
        (candidate_id,),
    ).fetchall()
    return [row_to_probe_result(row) for row in rows]


def replace_probe_results(
    conn: sqlite3.Connection,
    candidate_id: int,
    results: list[dict],
) -> list[CandidateProbeResult]:
    conn.execute("DELETE FROM candidate_probe_results WHERE candidate_id = ?", (candidate_id,))
    for result in results:
        conn.execute(
            """
            INSERT INTO candidate_probe_results (
                candidate_id,
                register_address,
                function_code,
                data_type,
                raw_value,
                decoded_value,
                valid,
                metric,
                scale,
                unit,
                quality,
                status,
                source,
                tested_json,
                inferred_json,
                failure_reason,
                exception_code,
                response_time_ms,
                validated_from_config,
                probe_profile_id,
                probe_profile_source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                result["register_address"],
                result["function_code"],
                result["data_type"],
                result.get("raw_value"),
                result.get("decoded_value"),
                int(result["valid"]),
                result.get("metric"),
                result.get("scale", 1.0),
                result.get("unit"),
                result.get("quality", "unknown"),
                result.get("status", "unknown"),
                result.get("source", "unknown"),
                result.get("tested_json", "{}"),
                result.get("inferred_json", "{}"),
                result.get("failure_reason"),
                result.get("exception_code"),
                result.get("response_time_ms"),
                int(result.get("validated_from_config", False)),
                result.get("probe_profile_id"),
                result.get("probe_profile_source"),
            ),
        )
    return list_probe_results(conn, candidate_id)


def update_candidate_probe_metadata(
    conn: sqlite3.Connection,
    candidate_id: int,
    *,
    metadata: dict,
) -> DiscoveredCandidate:
    conn.execute(
        """
        UPDATE discovered_candidates
        SET vendor_name = ?,
            product_code = ?,
            product_name = ?,
            model_name = ?,
            firmware_revision = ?,
            device_identification_raw = ?,
            vendor_identification_supported = ?,
            vendor_identification_error = ?,
            probe_profile_id = ?,
            probe_profile_source = ?,
            probe_quality = ?,
            probe_status = ?,
            probe_summary_json = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            metadata.get("vendor_name"),
            metadata.get("product_code"),
            metadata.get("product_name"),
            metadata.get("model_name"),
            metadata.get("firmware_revision"),
            metadata.get("device_identification_raw"),
            int(metadata.get("vendor_identification_supported", False)),
            metadata.get("vendor_identification_error"),
            metadata.get("probe_profile_id"),
            metadata.get("probe_profile_source"),
            metadata.get("probe_quality"),
            metadata.get("probe_status"),
            metadata.get("probe_summary_json"),
            candidate_id,
        ),
    )
    candidate = get_candidate(conn, candidate_id)
    if candidate is None:
        raise RuntimeError("Candidate disappeared during probe metadata update")
    return candidate


def update_candidate_fingerprint(
    conn: sqlite3.Connection,
    candidate_id: int,
    *,
    device_type_guess: str,
    confidence_score: float,
    vendor_guess: str,
    status: str = "reviewed",
) -> DiscoveredCandidate:
    conn.execute(
        """
        UPDATE discovered_candidates
        SET status = ?,
            device_type_guess = ?,
            confidence_score = ?,
            vendor_guess = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, device_type_guess, confidence_score, vendor_guess, candidate_id),
    )
    candidate = get_candidate(conn, candidate_id)
    if candidate is None:
        raise RuntimeError("Candidate disappeared during fingerprint update")
    return candidate


def reject_candidate(conn: sqlite3.Connection, candidate_id: int) -> Optional[DiscoveredCandidate]:
    if get_candidate(conn, candidate_id) is None:
        return None
    conn.execute(
        """
        UPDATE discovered_candidates
        SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (candidate_id,),
    )
    return get_candidate(conn, candidate_id)


def promote_candidate(
    conn: sqlite3.Connection,
    candidate: DiscoveredCandidate,
    payload: CandidatePromoteRequest,
) -> tuple[int, int]:
    cursor = conn.execute(
        """
        INSERT INTO devices (
            name,
            host,
            port,
            unit_id,
            description,
            location,
            enabled,
            poll_interval_sec,
            vendor_name,
            product_code,
            product_name,
            model_name,
            firmware_revision,
            device_identification_raw,
            probe_profile_id,
            probe_profile_source
        )
        VALUES (?, ?, ?, ?, ?, ?, 1, 30, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.device_name,
            candidate.ip_address,
            candidate.port,
            candidate.unit_id,
            payload.description or f"Promoted from discovered candidate #{candidate.id}",
            payload.location,
            candidate.vendor_name,
            candidate.product_code,
            candidate.product_name,
            candidate.model_name,
            candidate.firmware_revision,
            candidate.device_identification_raw,
            candidate.probe_profile_id,
            candidate.probe_profile_source,
        ),
    )
    device_id = cursor.lastrowid
    valid_results = [
        result for result in list_probe_results(conn, candidate.id)
        if result.valid and result.validated_from_config
    ]
    for result in valid_results:
        conn.execute(
            """
            INSERT INTO device_registers (
                device_id, metric, function_code, address, data_type, scale, unit, description, enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                device_id,
                result.metric or f"validated_{result.function_code}_{result.register_address}",
                result.function_code,
                result.register_address,
                result.data_type,
                result.scale,
                result.unit,
                "Validated from configured candidate probe result",
            ),
        )
    conn.execute(
        """
        UPDATE discovered_candidates
        SET status = 'promoted', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (candidate.id,),
    )
    return device_id, len(valid_results)
