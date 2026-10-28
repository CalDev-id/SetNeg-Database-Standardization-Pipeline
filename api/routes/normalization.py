"""Endpoint tahap Normalisasi Database."""

import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from features.audit_db.audit_output import combined_findings
from features.audit_db.pipeline import find_spreadsheet_job
from features.normalization.pipeline import (
    find_normalization_job, get_normalization_runtime, start_normalization_job,
)


router = APIRouter()


class NormalizationRequest(BaseModel):
    audit_job_id: str
    model: str = "telkom"


@router.post("", status_code=202)
async def create_normalization(data: NormalizationRequest, request: Request) -> dict:
    audit_job = find_spreadsheet_job(data.audit_job_id)
    if not audit_job:
        raise HTTPException(status_code=404, detail="Hasil audit tidak ditemukan atau sudah kedaluwarsa.")
    if audit_job.status not in {"queued", "running", "completed"}:
        raise HTTPException(status_code=409, detail="Audit Database gagal. Unggah ulang DDL untuk memulai normalisasi.")
    try:
        runtime = get_normalization_runtime(data.model)
        job_id = await start_normalization_job(
            audit_job.source_ddl, audit_job.source_filename, data.audit_job_id,
            runtime, request.app.state.audit_semaphore,
        )
        audit_job.normalization_job_id = job_id
        audit_job.normalization_error = None
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/api/v1/normalization/{job_id}",
    }


@router.get("/{job_id}")
async def get_normalization(job_id: str) -> dict:
    job = find_normalization_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan normalisasi tidak ditemukan atau sudah kedaluwarsa.")
    completed = job.status == "completed"
    audit_job = find_spreadsheet_job(job.audit_job_id)
    return {
        "job_id": job_id,
        "audit_job_id": job.audit_job_id,
        "status": job.status,
        "completed_batches": job.completed_batches,
        "total_batches": job.total_batches,
        "elapsed_seconds": int((job.finished_at or time.monotonic()) - job.started_at),
        "source_filename": job.source_filename,
        "table_count": job.table_count,
        "column_count": job.column_count,
        "finding_count": len(job.findings) if completed else None,
        "error": job.error,
        "process_events": audit_job.process_events or [] if audit_job else [],
        "findings_url": f"/api/v1/normalization/{job_id}/findings" if completed else None,
        "download_url": f"/api/v1/normalization/{job_id}/download" if completed else None,
    }


@router.get("/{job_id}/findings")
async def get_normalization_findings(job_id: str) -> dict:
    job = find_normalization_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan normalisasi tidak ditemukan atau sudah kedaluwarsa.")
    if job.status != "completed" or job.findings is None:
        raise HTTPException(status_code=409, detail="Normalisasi belum selesai. Periksa status pekerjaan.")
    return {
        "summary": {"table_count": job.table_count, "column_count": job.column_count,
                    "finding_count": len(job.findings)},
        "findings": job.findings,
        "display_findings": combined_findings([], job.findings),
    }


@router.get("/{job_id}/download")
async def download_normalization(job_id: str) -> Response:
    job = find_normalization_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan normalisasi tidak ditemukan atau sudah kedaluwarsa.")
    if job.status != "completed" or job.excel is None:
        raise HTTPException(status_code=409, detail=job.error or "Normalisasi belum selesai. Periksa status pekerjaan.")
    return Response(
        content=job.excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="temuan_normalisasi.xlsx"'},
    )
