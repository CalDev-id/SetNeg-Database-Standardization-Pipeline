"""Endpoint pembuatan dan unduhan DDL Standar."""

import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from features.audit_db.pipeline import find_spreadsheet_job
from features.data_dictionary.pipeline import find_new_dictionary_job, find_old_dictionary_job
from features.ddl_standard.pipeline import find_ddl_standard_job, start_ddl_standard_job


router = APIRouter()


class DdlStandardRequest(BaseModel):
    audit_job_id: str
    old_dictionary_job_id: str
    new_dictionary_job_id: str
    model: str = "telkom"


@router.post("", status_code=202)
async def create_ddl_standard(data: DdlStandardRequest, request: Request) -> dict:
    audit_job = find_spreadsheet_job(data.audit_job_id)
    old_job = find_old_dictionary_job(data.old_dictionary_job_id)
    new_job = find_new_dictionary_job(data.new_dictionary_job_id)
    if not audit_job or not old_job or not new_job:
        raise HTTPException(status_code=404, detail="Input DDL Standar tidak ditemukan atau sudah kedaluwarsa.")
    if audit_job.status != "completed" or any(
        job.status != "completed" or job.result is None for job in (old_job, new_job)
    ):
        raise HTTPException(status_code=409, detail="Dictionary Old dan Dictionary New harus selesai terlebih dahulu.")
    if old_job.audit_job_id != data.audit_job_id or new_job.audit_job_id != data.audit_job_id:
        raise HTTPException(status_code=422, detail="Input harus berasal dari audit yang sama.")
    try:
        job_id = await start_ddl_standard_job(
            audit_job.source_ddl, old_job.result, new_job.result, data.model,
            request.app.state.audit_semaphore, data.audit_job_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"job_id": job_id, "status": "queued", "status_url": f"/api/v1/ddl-standard/{job_id}"}


@router.get("/{job_id}")
async def get_ddl_standard(job_id: str) -> dict:
    job = find_ddl_standard_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan DDL Standar tidak ditemukan atau sudah kedaluwarsa.")
    return {
        "status": job.status,
        "completed_objects": job.completed_objects,
        "total_objects": job.total_objects,
        "elapsed_seconds": int((job.finished_at or time.monotonic()) - job.started_at),
        "error": job.error,
        "result": job.result if job.status == "completed" else None,
    }


@router.get("/{job_id}/download/{kind}")
async def download_ddl_standard(job_id: str, kind: str) -> Response:
    if kind not in {"alter", "create"}:
        raise HTTPException(status_code=404, detail="Jenis DDL tidak dikenal.")
    job = find_ddl_standard_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan DDL Standar tidak ditemukan atau sudah kedaluwarsa.")
    if job.status != "completed" or job.result is None:
        raise HTTPException(status_code=409, detail="DDL Standar belum selesai.")
    return Response(
        content=job.result[f"ddl_{kind}"], media_type="application/sql; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="ddl_{kind}.sql"'},
    )
