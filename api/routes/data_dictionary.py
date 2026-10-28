"""Endpoint tahapan Data Dictionary."""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from features.audit_db.extract import DdlValidationError
from features.audit_db.pipeline import find_spreadsheet_job
from features.normalization.pipeline import NormalizationJob, find_normalization_job
from features.data_dictionary.pipeline import (
    find_classification_job, find_old_dictionary_job, find_new_dictionary_job,
    start_classification_job, start_old_dictionary_job, start_new_dictionary_job,
    find_log_perubahan_job, start_log_perubahan_job,
)


router = APIRouter()


def require_completed_normalization(normalization_job_id: str, audit_job_id: str) -> NormalizationJob:
    job = find_normalization_job(normalization_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Hasil normalisasi tidak ditemukan atau sudah kedaluwarsa.")
    if job.audit_job_id != audit_job_id:
        raise HTTPException(status_code=422, detail="Hasil normalisasi tidak berasal dari audit yang dipilih.")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Normalisasi Database harus selesai terlebih dahulu.")
    return job


class ClassificationRequest(BaseModel):
    audit_job_id: str
    normalization_job_id: str


@router.post("/classification", status_code=202)
async def create_classification(data: ClassificationRequest, request: Request) -> dict:
    audit_job = find_spreadsheet_job(data.audit_job_id)
    if not audit_job:
        raise HTTPException(status_code=404, detail="Hasil audit tidak ditemukan atau sudah kedaluwarsa.")
    if audit_job.status != "completed" or audit_job.audit_result is None:
        raise HTTPException(status_code=409, detail="Audit Database harus selesai terlebih dahulu.")
    require_completed_normalization(data.normalization_job_id, data.audit_job_id)

    try:
        job_id = await start_classification_job(
            audit_job.source_ddl,
            audit_job.audit_result["findings"],
            request.app.state.audit_semaphore,
            data.audit_job_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/api/v1/data-dictionary/classification/{job_id}",
    }


@router.get("/classification/{job_id}")
async def get_classification(job_id: str) -> dict:
    job = find_classification_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan klasifikasi tidak ditemukan atau sudah kedaluwarsa.")
    return {
        "status": job.status,
        "completed_tables": job.completed_tables,
        "total_tables": job.total_tables,
        "elapsed_seconds": int((job.finished_at or time.monotonic()) - job.started_at),
        "error": job.error,
        "result": job.result if job.status == "completed" else None,
    }


class OldDictionaryRequest(BaseModel):
    audit_job_id: str
    normalization_job_id: str
    model: str = "telkom"


@router.post("/old-dictionary", status_code=202)
async def create_old_dictionary(data: OldDictionaryRequest, request: Request) -> dict:
    audit_job = find_spreadsheet_job(data.audit_job_id)
    if not audit_job:
        raise HTTPException(status_code=404, detail="DDL sumber tidak ditemukan atau sudah kedaluwarsa.")
    if audit_job.status != "completed":
        raise HTTPException(status_code=409, detail="Audit Database harus selesai terlebih dahulu.")
    require_completed_normalization(data.normalization_job_id, data.audit_job_id)
    try:
        job_id = await start_old_dictionary_job(
            audit_job.source_ddl, data.model, request.app.state.audit_semaphore, data.audit_job_id,
        )
    except (DdlValidationError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/api/v1/data-dictionary/old-dictionary/{job_id}",
    }


@router.get("/old-dictionary/{job_id}")
async def get_old_dictionary(job_id: str) -> dict:
    job = find_old_dictionary_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan Old Dictionary tidak ditemukan atau sudah kedaluwarsa.")
    return {
        "status": job.status,
        "completed_objects": job.completed_objects,
        "total_objects": job.total_objects,
        "elapsed_seconds": int((job.finished_at or time.monotonic()) - job.started_at),
        "error": job.error,
        "result": job.result if job.status == "completed" else None,
    }


class NewDictionaryRequest(BaseModel):
    audit_job_id: str
    normalization_job_id: str
    classification_job_id: str
    model: str = "telkom"
    retry_job_id: Optional[str] = None


@router.post("/new-dictionary", status_code=202)
async def create_new_dictionary(data: NewDictionaryRequest, request: Request) -> dict:
    previous = find_new_dictionary_job(data.retry_job_id) if data.retry_job_id else None
    if data.retry_job_id and previous is None:
        raise HTTPException(status_code=404, detail="Checkpoint Dictionary New tidak ditemukan atau sudah kedaluwarsa.")
    if previous is not None:
        if previous.status != "failed" or previous.audit_job_id != data.audit_job_id:
            raise HTTPException(status_code=422, detail="Checkpoint Dictionary New tidak sesuai dengan audit.")
        if previous.model != data.model:
            raise HTTPException(status_code=422, detail="Model berubah; gunakan model semula untuk melanjutkan batch.")
    if previous and all(value is not None for value in (
        previous.source_ddl, previous.findings, previous.normalization_findings,
        previous.classification,
    )):
        source_ddl = previous.source_ddl
        findings = previous.findings
        normalization_findings = previous.normalization_findings
        classification = previous.classification
    else:
        audit_job = find_spreadsheet_job(data.audit_job_id)
        classification_job = find_classification_job(data.classification_job_id)
        if not audit_job or not classification_job:
            raise HTTPException(status_code=404, detail="Hasil audit atau klasifikasi tidak ditemukan atau sudah kedaluwarsa.")
        if audit_job.status != "completed" or audit_job.audit_result is None:
            raise HTTPException(status_code=409, detail="Audit Database harus selesai terlebih dahulu.")
        normalization_job = require_completed_normalization(data.normalization_job_id, data.audit_job_id)
        if normalization_job.findings is None:
            raise HTTPException(status_code=409, detail="Hasil Normalisasi Database belum tersedia.")
        if classification_job.status != "completed" or classification_job.result is None:
            raise HTTPException(status_code=409, detail="Klasifikasi tabel harus selesai terlebih dahulu.")
        if classification_job.audit_job_id != data.audit_job_id:
            raise HTTPException(status_code=422, detail="Hasil klasifikasi tidak berasal dari audit yang dipilih.")
        source_ddl = audit_job.source_ddl
        findings = audit_job.audit_result["findings"]
        normalization_findings = normalization_job.findings
        classification = classification_job.result
    try:
        job_id = await start_new_dictionary_job(
            source_ddl, findings, normalization_findings, classification,
            data.model, request.app.state.audit_semaphore, data.audit_job_id,
            data.retry_job_id,
        )
    except (DdlValidationError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/api/v1/data-dictionary/new-dictionary/{job_id}",
    }


@router.get("/new-dictionary/{job_id}")
async def get_new_dictionary(job_id: str) -> dict:
    job = find_new_dictionary_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan Dictionary New tidak ditemukan atau sudah kedaluwarsa.")
    return {
        "status": job.status,
        "completed_batches": max(job.completed_batches, len(job.checkpoint)),
        "total_batches": job.total_batches,
        "saved_batches": len(job.checkpoint),
        "elapsed_seconds": int((job.finished_at or time.monotonic()) - job.started_at),
        "error": job.error,
        "error_reason": job.error_reason,
        "result": job.result if job.status == "completed" else None,
    }


class LogPerubahanRequest(BaseModel):
    audit_job_id: str
    normalization_job_id: str
    old_dictionary_job_id: str
    new_dictionary_job_id: str
    model: str = "telkom"


@router.post("/log-perubahan", status_code=202)
async def create_log_perubahan(data: LogPerubahanRequest, request: Request) -> dict:
    audit_job = find_spreadsheet_job(data.audit_job_id)
    old_job = find_old_dictionary_job(data.old_dictionary_job_id)
    new_job = find_new_dictionary_job(data.new_dictionary_job_id)
    if not audit_job or not old_job or not new_job:
        raise HTTPException(status_code=404, detail="Hasil audit atau dictionary tidak ditemukan atau sudah kedaluwarsa.")
    if audit_job.status != "completed" or audit_job.audit_result is None:
        raise HTTPException(status_code=409, detail="Audit Database harus selesai terlebih dahulu.")
    normalization_job = require_completed_normalization(data.normalization_job_id, data.audit_job_id)
    if normalization_job.findings is None:
        raise HTTPException(status_code=409, detail="Hasil Normalisasi Database belum tersedia.")
    if any(job.status != "completed" or job.result is None for job in (old_job, new_job)):
        raise HTTPException(status_code=409, detail="Dictionary Old dan Dictionary New harus selesai terlebih dahulu.")
    if old_job.audit_job_id != data.audit_job_id or new_job.audit_job_id != data.audit_job_id:
        raise HTTPException(status_code=422, detail="Kedua dictionary harus berasal dari audit yang sama.")
    try:
        job_id = await start_log_perubahan_job(
            old_job.result, new_job.result, audit_job.audit_result["findings"],
            data.model, request.app.state.audit_semaphore,
            normalization_job.findings,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/api/v1/data-dictionary/log-perubahan/{job_id}",
    }


@router.get("/log-perubahan/{job_id}")
async def get_log_perubahan(job_id: str) -> dict:
    job = find_log_perubahan_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan Log Perubahan tidak ditemukan atau sudah kedaluwarsa.")
    return {
        "status": job.status,
        "completed_batches": job.completed_batches,
        "total_batches": job.total_batches,
        "elapsed_seconds": int((job.finished_at or time.monotonic()) - job.started_at),
        "error": job.error,
        "result": job.result if job.status == "completed" else None,
    }
