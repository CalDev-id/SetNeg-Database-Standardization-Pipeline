import time

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from features.audit_db.pipeline import AuditError, process_schema_audit
from shared.jobs.audit_queue import find_spreadsheet_job, start_spreadsheet_job
from shared.llm.runtime import get_runtime
from shared.ddl.parser import DdlValidationError

router = APIRouter()


class AuditSummary(BaseModel):
    table_count: int = Field(ge=1)
    column_count: int = Field(ge=1)
    tables: list[str]


class TemuanResponse(BaseModel):
    no: int = Field(ge=1)
    nama_tabel: str
    objek_temuan: str
    aturan_playbook: str
    uraian_ketidaksesuaian: str
    solusi: str
    status: str
    catatan: str
    status_pii: str


class AuditResponse(BaseModel):
    message: str
    summary: AuditSummary
    findings: list[TemuanResponse]


@router.post("", response_model=AuditResponse)
async def create_audit(
    file: UploadFile = File(...), model: str = Form("qwen"),
) -> AuditResponse:
    if not file.filename or not file.filename.lower().endswith((".sql", ".ddl")):
        raise HTTPException(status_code=415, detail="File harus berformat .sql atau .ddl.")

    content = await file.read()
    try:
        result = await process_schema_audit(content, "json", runtime=get_runtime(model))
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
    model: str = Form("qwen"),
) -> dict:
    if not file.filename or not file.filename.lower().endswith((".sql", ".ddl")):
        raise HTTPException(status_code=415, detail="File harus berformat .sql atau .ddl.")
    content = await file.read()
    try:
        runtime = get_runtime(model)
        job_id = await start_spreadsheet_job(
            content, request.app.state.audit_semaphore, runtime,
        )
    except DdlValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "job_id": job_id,
        "status": "queued",
        "tracking_url": f"/?job_id={job_id}",
        "status_url": f"/api/v1/audit/spreadsheet/{job_id}",
        "download_url": f"/api/v1/audit/spreadsheet/{job_id}/download",
    }


@router.get("/spreadsheet/{job_id}")
async def get_audit_spreadsheet_job(job_id: str) -> dict:
    job = find_spreadsheet_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan atau sudah kedaluwarsa.")
    return {
        "status": job.status,
        "completed_batches": job.completed_batches,
        "total_batches": job.total_batches,
        "elapsed_seconds": int(time.monotonic() - job.started_at),
        "error": job.error,
        "download_url": f"/api/v1/audit/spreadsheet/{job_id}/download" if job.status == "completed" else None,
    }


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
