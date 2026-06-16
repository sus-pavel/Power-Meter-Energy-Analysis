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
                candidate_id, register_address, function_code, data_type, raw_value, decoded_value, valid
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                result["register_address"],
                result["function_code"],
                result["data_type"],
                result.get("raw_value"),
                result.get("decoded_value"),
                int(result["valid"]),
            ),
        )
    return list_probe_results(conn, candidate_id)


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
        INSERT INTO devices (name, host, port, unit_id, description, location, enabled)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (
            payload.device_name,
            candidate.ip_address,
            candidate.port,
            candidate.unit_id,
            payload.description or f"Promoted from discovered candidate #{candidate.id}",
            payload.location,
        ),
    )
    device_id = cursor.lastrowid
    valid_results = [
        result for result in list_probe_results(conn, candidate.id)
        if result.valid
    ]
    for result in valid_results:
        conn.execute(
            """
            INSERT INTO device_registers (
                device_id, metric, function_code, address, data_type, scale, unit, description, enabled
            )
            VALUES (?, ?, ?, ?, ?, 1.0, NULL, ?, 1)
            """,
            (
                device_id,
                f"probed_{result.function_code}_{result.register_address}",
                result.function_code,
                result.register_address,
                result.data_type,
                "Promoted from candidate probe result",
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
