import logging
import time
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from features.audit_db.audit import AuditError
from features.audit_db.extract import DdlValidationError
from features.audit_db.audit_output import buat_excel_gabungan, combined_findings
from features.audit_db.pipeline import (
    find_spreadsheet_job,
    process_schema_audit,
    retry_spreadsheet_job,
    start_spreadsheet_job,
)
from features.normalization.pipeline import (
    find_normalization_job, get_normalization_runtime, start_normalization_job,
)
from shared.llm.runtime import get_runtime

router = APIRouter()
logger = logging.getLogger(__name__)


def get_audit_runtime(model: str):
    runtime = get_runtime(model)
    if model == "gpt_setneg":
        runtime.max_attempts = 1
        runtime.timeout_seconds = (10, 300)
    return runtime


class AuditSummary(BaseModel):
    table_count: int = Field(ge=1)
    column_count: int = Field(ge=1)
    tables: list[str]


class TemuanResponse(BaseModel):
    no: int = Field(ge=1)
    nama_database: str
    nama_tabel: str
    objek_temuan: str
    aturan_playbook: str
    uraian_ketidaksesuaian: str
    solusi: str
    status: str
    catatan: str


class AuditResponse(BaseModel):
    message: str
    summary: AuditSummary
    findings: list[TemuanResponse]


@router.post("", response_model=AuditResponse)
async def create_audit(
    file: UploadFile = File(...), model: str = Form("telkom"),
) -> AuditResponse:
    if not file.filename or not file.filename.lower().endswith((".sql", ".ddl")):
        raise HTTPException(status_code=415, detail="File harus berformat .sql atau .ddl.")

    content = await file.read()
    try:
        result = await process_schema_audit(content, "json", runtime=get_audit_runtime(model))
    except DdlValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except AuditError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    return AuditResponse(**result)


@router.post("/spreadsheet", status_code=202)
async def create_audit_spreadsheet(
    request: Request,
    file: UploadFile = File(...),
    model: str = Form("telkom"),
) -> dict:
    if not file.filename or not file.filename.lower().endswith((".sql", ".ddl")):
        raise HTTPException(status_code=415, detail="File harus berformat .sql atau .ddl.")
    content = await file.read()
    try:
        runtime = get_audit_runtime(model)
        job_id = await start_spreadsheet_job(
            content, file.filename, request.app.state.audit_semaphore, runtime,
        )
    except DdlValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    audit_job = find_spreadsheet_job(job_id)
    try:
        normalization_id = await start_normalization_job(
            content, file.filename, job_id, get_normalization_runtime(model), request.app.state.audit_semaphore,
        )
        audit_job.normalization_job_id = normalization_id
    except Exception:
        logger.exception("Normalisasi untuk audit %s gagal dimulai", job_id)
        audit_job.normalization_error = "Normalisasi gagal dimulai. Coba lagi dari tahap Normalisasi Database."
    return {
        "job_id": job_id,
        "status": "queued",
        "tracking_url": f"/?job_id={job_id}",
        "status_url": f"/api/v1/audit/spreadsheet/{job_id}",
        "download_url": f"/api/v1/audit/spreadsheet/{job_id}/download",
        "findings_url": f"/api/v1/audit/spreadsheet/{job_id}/findings",
        "source_url": f"/api/v1/audit/spreadsheet/{job_id}/source",
        "source_filename": file.filename,
        "normalization_job_id": audit_job.normalization_job_id,
        "normalization_status_url": (
            f"/api/v1/normalization/{audit_job.normalization_job_id}"
            if audit_job.normalization_job_id else None
        ),
        "normalization_error": audit_job.normalization_error,
    }


@router.get("/spreadsheet/{job_id}")
async def get_audit_spreadsheet_job(job_id: str) -> dict:
    job = find_spreadsheet_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan atau sudah kedaluwarsa.")
    return {
        "job_id": job_id,
        "status": job.status,
        "completed_batches": job.completed_batches,
        "total_batches": job.total_batches,
        "elapsed_seconds": int((job.finished_at or time.monotonic()) - job.started_at),
        "error": job.error,
        "retry_available": job.status == "failed" and job.parsed_ddl is not None and job.runtime is not None,
        "process_events": job.process_events or [],
        "download_url": f"/api/v1/audit/spreadsheet/{job_id}/download" if job.status == "completed" else None,
        "findings_url": f"/api/v1/audit/spreadsheet/{job_id}/findings" if job.status == "completed" else None,
        "source_url": f"/api/v1/audit/spreadsheet/{job_id}/source" if job.status == "completed" else None,
        "source_filename": job.source_filename,
        "normalization_job_id": job.normalization_job_id,
        "normalization_status_url": (
            f"/api/v1/normalization/{job.normalization_job_id}"
            if job.normalization_job_id else None
        ),
        "normalization_error": job.normalization_error,
    }


@router.post("/spreadsheet/{job_id}/retry", status_code=202)
async def retry_audit_spreadsheet_job(job_id: str, request: Request) -> dict:
    try:
        job = retry_spreadsheet_job(job_id, request.app.state.audit_semaphore)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {
        "job_id": job_id,
        "status": job.status,
        "status_url": f"/api/v1/audit/spreadsheet/{job_id}",
        "completed_batches": job.completed_batches,
        "total_batches": job.total_batches,
    }


@router.get("/spreadsheet/{job_id}/findings", response_model=AuditResponse)
async def get_audit_spreadsheet_findings(job_id: str) -> AuditResponse:
    job = find_spreadsheet_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan atau sudah kedaluwarsa.")
    if job.status != "completed" or job.audit_result is None:
        raise HTTPException(status_code=409, detail="Analisis belum selesai. Periksa status pekerjaan.")
    return AuditResponse(**job.audit_result)


@router.get("/spreadsheet/{job_id}/download")
async def download_audit_spreadsheet_job(job_id: str) -> Response:
    job = find_spreadsheet_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan atau sudah kedaluwarsa.")
    if job.status == "failed":
        raise HTTPException(status_code=409, detail=job.error)
    if job.status != "completed" or job.result is None:
        raise HTTPException(status_code=409, detail="Analisis belum selesai. Periksa status pekerjaan.")
    return Response(
        content=job.result,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="temuan_standardisasi.xlsx"'},
    )


def _combined_rows(job_id: str) -> list[dict]:
    job = find_spreadsheet_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan atau sudah kedaluwarsa.")
    if job.status != "completed" or job.audit_result is None:
        raise HTTPException(status_code=409, detail=job.error or "Audit Database belum selesai.")
    normalization = find_normalization_job(job.normalization_job_id) if job.normalization_job_id else None
    if not normalization or normalization.audit_job_id != job_id:
        raise HTTPException(status_code=409, detail="Hasil Normalisasi Database belum tersedia.")
    if normalization.status != "completed" or normalization.findings is None:
        raise HTTPException(status_code=409, detail=normalization.error or "Normalisasi Database belum selesai.")
    return combined_findings(job.audit_result["findings"], normalization.findings)


@router.get("/spreadsheet/{job_id}/combined-findings")
async def get_combined_findings(job_id: str) -> dict:
    findings = _combined_rows(job_id)
    job = find_spreadsheet_job(job_id)
    return {"summary": job.audit_result["summary"], "findings": findings}


@router.get("/spreadsheet/{job_id}/download/combined")
async def download_combined_findings(job_id: str) -> Response:
    content = buat_excel_gabungan(_combined_rows(job_id))
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="temuan_audit_normalisasi.xlsx"'},
    )


@router.get("/spreadsheet/{job_id}/source")
async def download_audit_source_ddl(job_id: str) -> Response:
    job = find_spreadsheet_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan atau sudah kedaluwarsa.")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Analisis belum selesai. Periksa status pekerjaan.")

    filename = Path(job.source_filename).name or "schema.sql"
    return Response(
        content=job.source_ddl,
        media_type="application/sql",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
