"""Pekerjaan asynchronous untuk tahapan Data Dictionary."""

import asyncio
import copy
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from features.audit_db.audit import LlmRuntime
from features.audit_db.extract import ParsedDdl, parse_schema_ddl
from features.audit_db.pipeline import JOB_TTL_SECONDS
from features.data_dictionary.dictionary_old import OldDictionaryError, build_old_dictionary, parse_existing_objects
from features.data_dictionary.dictionary_new import (
    MAX_COLUMNS_PER_BATCH as NEW_MAX_COLUMNS_PER_BATCH,
    PROMPT_PERUBAHAN, NewDictionaryError, build_new_dictionary, count_batches,
)
from features.data_dictionary.log_perubahan import LogPerubahanError, build_log_perubahan, count_log_batches
from features.data_dictionary.table_classification import ClassificationError, classify_tables
from shared.batching import MAX_MERGED_REMAINDER
from shared.llm.runtime import get_runtime


logger = logging.getLogger(__name__)


def dictionary_error_reason(error: Exception) -> str:
    """Expose a short cause while keeping full LLM output in server logs."""
    detail = str(error).lower()
    if "timeout" in detail or "batas waktu" in detail:
        return "Layanan LLM melewati batas waktu."
    if "http 429" in detail:
        return "Layanan LLM membatasi jumlah permintaan."
    if any(f"http {status}" in detail for status in (500, 502, 503, 504, 524)):
        return "Layanan LLM sedang bermasalah."
    if "batas token" in detail:
        return "Batas token respons LLM tercapai."
    if "respons kosong" in detail:
        return "Layanan LLM mengembalikan respons kosong."
    if "koneksi" in detail or "connection" in detail:
        return "Koneksi ke layanan LLM gagal."
    if any(word in detail for word in ("format", "json", "kolom", "tabel", "valid")):
        return "Struktur respons LLM tidak sesuai."
    return "Respons LLM atau layanan tidak dapat diproses."


def get_dictionary_runtime(model: str, *, heavy: bool = False) -> LlmRuntime:
    """Sesuaikan waktu tunggu Telkom dengan ukuran pekerjaan Dictionary."""
    runtime = get_runtime(model)
    if model == "telkom" and hasattr(runtime, "max_attempts"):
        runtime.max_attempts = min(runtime.max_attempts, 2)
        if hasattr(runtime, "read_timeout_seconds"):
            runtime.read_timeout_seconds = 180 if heavy else 90
    return runtime


@dataclass
class ClassificationJob:
    status: str
    completed_tables: int
    total_tables: int
    started_at: float
    audit_job_id: str
    result: Optional[dict[str, dict]] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None


_jobs: dict[str, ClassificationJob] = {}
_tasks: set[asyncio.Task] = set()


async def start_classification_job(
    source_ddl: bytes, findings: list[dict], semaphore: asyncio.Semaphore,
    audit_job_id: str,
) -> str:
    parsed_ddl = await asyncio.to_thread(parse_schema_ddl, source_ddl)
    runtime = get_dictionary_runtime("telkom")
    for old_id, job in list(_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _jobs[old_id]

    job_id = uuid4().hex
    _jobs[job_id] = ClassificationJob("queued", 0, len(parsed_ddl.tables), time.monotonic(), audit_job_id)
    task = asyncio.create_task(_run_job(job_id, parsed_ddl, findings, runtime, semaphore))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_job(
    job_id: str, parsed_ddl: ParsedDdl, findings: list[dict],
    runtime: LlmRuntime, semaphore: asyncio.Semaphore,
) -> None:
    job = _jobs[job_id]
    async with semaphore:
        job.status = "running"

        def table_complete() -> None:
            job.completed_tables += 1

        try:
            job.result = await classify_tables(
                parsed_ddl, findings, runtime, on_table_complete=table_complete,
            )
            job.status = "completed"
        except ClassificationError as error:
            logger.warning("Pekerjaan klasifikasi %s gagal: %s", job_id, error)
            job.error = "Klasifikasi gagal. Coba lagi."
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan klasifikasi %s gagal", job_id)
            job.error = "Klasifikasi gagal. Coba lagi."
            job.status = "failed"
        finally:
            job.finished_at = time.monotonic()


def find_classification_job(job_id: str) -> Optional[ClassificationJob]:
    job = _jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _jobs.pop(job_id, None)
        return None
    return job


@dataclass
class OldDictionaryJob:
    status: str
    completed_objects: int
    total_objects: int
    started_at: float
    audit_job_id: str
    result: Optional[dict[str, dict]] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None


_old_jobs: dict[str, OldDictionaryJob] = {}


async def start_old_dictionary_job(source_ddl: bytes, model: str, semaphore: asyncio.Semaphore,
                                   audit_job_id: str) -> str:
    objects = await asyncio.to_thread(parse_existing_objects, source_ddl)
    runtime = get_dictionary_runtime(model)
    for old_id, job in list(_old_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _old_jobs[old_id]

    job_id = uuid4().hex
    _old_jobs[job_id] = OldDictionaryJob("queued", 0, len(objects), time.monotonic(), audit_job_id)
    task = asyncio.create_task(_run_old_dictionary_job(job_id, source_ddl, runtime, semaphore))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_old_dictionary_job(
    job_id: str, source_ddl: bytes, runtime: LlmRuntime, semaphore: asyncio.Semaphore,
) -> None:
    job = _old_jobs[job_id]
    async with semaphore:
        job.status = "running"

        def object_complete() -> None:
            job.completed_objects += 1

        try:
            job.result = await build_old_dictionary(source_ddl, runtime, object_complete)
            job.status = "completed"
        except OldDictionaryError as error:
            logger.warning("Pekerjaan Old Dictionary %s gagal: %s", job_id, error)
            job.error = "Dictionary Old gagal. Coba lagi."
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan Old Dictionary %s gagal", job_id)
            job.error = "Dictionary Old gagal. Coba lagi."
            job.status = "failed"
        finally:
            job.finished_at = time.monotonic()


def find_old_dictionary_job(job_id: str) -> Optional[OldDictionaryJob]:
    job = _old_jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _old_jobs.pop(job_id, None)
        return None
    return job


@dataclass
class NewDictionaryJob:
    status: str
    completed_batches: int
    total_batches: int
    started_at: float
    audit_job_id: str
    input_key: str
    checkpoint: dict[tuple[str, int], tuple[str, dict, dict]] = field(default_factory=dict)
    result: Optional[dict[str, dict]] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None
    source_ddl: Optional[bytes] = None
    findings: Optional[list[dict]] = None
    normalization_findings: Optional[list[dict]] = None
    classification: Optional[dict[str, dict]] = None
    model: Optional[str] = None
    error_reason: Optional[str] = None


_new_jobs: dict[str, NewDictionaryJob] = {}


async def start_new_dictionary_job(
    source_ddl: bytes, findings: list[dict], normalization_findings: list[dict],
    classification: dict[str, dict],
    model: str, semaphore: asyncio.Semaphore,
    audit_job_id: str,
    retry_job_id: Optional[str] = None,
) -> str:
    objects = await asyncio.to_thread(parse_existing_objects, source_ddl)
    runtime = get_dictionary_runtime(model, heavy=True)
    fingerprint = hashlib.sha256(source_ddl)
    fingerprint.update(json.dumps(
        [findings, normalization_findings, classification, model,
         getattr(runtime, "model", None), PROMPT_PERUBAHAN,
         NEW_MAX_COLUMNS_PER_BATCH, MAX_MERGED_REMAINDER],
        ensure_ascii=False, sort_keys=True,
    ).encode("utf-8"))
    input_key = fingerprint.hexdigest()
    for old_id, job in list(_new_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _new_jobs[old_id]

    if retry_job_id:
        previous = find_new_dictionary_job(retry_job_id)
        if not previous or previous.audit_job_id != audit_job_id or previous.status != "failed":
            raise ValueError("Checkpoint Dictionary New tidak tersedia. Mulai ulang tahap Dictionary New.")
        if previous.input_key != input_key:
            raise ValueError("Input atau model berubah; batch Dictionary New sebelumnya tidak bisa dipakai ulang.")
    else:
        previous = max(
            (job for job in reversed(list(_new_jobs.values()))
             if job.audit_job_id == audit_job_id and job.input_key == input_key
             and job.status == "failed"),
            key=lambda job: len(job.checkpoint), default=None,
        )
    job_id = uuid4().hex
    _new_jobs[job_id] = NewDictionaryJob(
        "queued", 0, count_batches(objects, findings), time.monotonic(), audit_job_id,
        input_key, copy.deepcopy(previous.checkpoint) if previous else {},
        source_ddl=source_ddl, findings=findings,
        normalization_findings=normalization_findings,
        classification=classification, model=model,
    )
    task = asyncio.create_task(_run_new_dictionary_job(
        job_id, source_ddl, findings, normalization_findings, classification, runtime, semaphore,
    ))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_new_dictionary_job(
    job_id: str, source_ddl: bytes, findings: list[dict], normalization_findings: list[dict],
    classification: dict[str, dict],
    runtime: LlmRuntime, semaphore: asyncio.Semaphore,
) -> None:
    job = _new_jobs[job_id]
    async with semaphore:
        job.status = "running"

        def batch_complete() -> None:
            job.completed_batches += 1

        try:
            job.result = await build_new_dictionary(
                source_ddl, findings, normalization_findings, classification, runtime,
                batch_complete, job.checkpoint,
            )
            job.checkpoint.clear()
            job.status = "completed"
        except NewDictionaryError as error:
            logger.warning("Pekerjaan Dictionary New %s gagal: %s", job_id, error)
            job.error = "Dictionary New gagal. Coba lagi."
            job.error_reason = dictionary_error_reason(error)
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan Dictionary New %s gagal", job_id)
            job.error = "Dictionary New gagal. Coba lagi."
            job.error_reason = "Kesalahan internal saat memproses batch."
            job.status = "failed"
        finally:
            job.finished_at = time.monotonic()


def find_new_dictionary_job(job_id: str) -> Optional[NewDictionaryJob]:
    job = _new_jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _new_jobs.pop(job_id, None)
        return None
    return job


@dataclass
class LogPerubahanJob:
    status: str
    completed_batches: int
    total_batches: int
    started_at: float
    result: Optional[dict[str, list[dict]]] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None


_log_jobs: dict[str, LogPerubahanJob] = {}


async def start_log_perubahan_job(
    old_dictionary: dict[str, dict], new_dictionary: dict[str, dict], findings: list[dict],
    model: str, semaphore: asyncio.Semaphore,
    normalization_findings: Optional[list[dict]] = None,
) -> str:
    runtime = get_dictionary_runtime(model, heavy=True)
    for old_id, job in list(_log_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _log_jobs[old_id]
    job_id = uuid4().hex
    _log_jobs[job_id] = LogPerubahanJob("queued", 0, count_log_batches(new_dictionary), time.monotonic())
    task = asyncio.create_task(_run_log_perubahan_job(
        job_id, old_dictionary, new_dictionary, findings, runtime, semaphore,
        normalization_findings or [],
    ))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_log_perubahan_job(
    job_id: str, old_dictionary: dict[str, dict], new_dictionary: dict[str, dict],
    findings: list[dict], runtime: LlmRuntime, semaphore: asyncio.Semaphore,
    normalization_findings: list[dict],
) -> None:
    job = _log_jobs[job_id]
    async with semaphore:
        job.status = "running"

        def batch_complete() -> None:
            job.completed_batches += 1

        try:
            job.result = await build_log_perubahan(
                old_dictionary, new_dictionary, findings, runtime, batch_complete,
                normalization_findings,
            )
            job.status = "completed"
        except LogPerubahanError as error:
            logger.warning("Pekerjaan Log Perubahan %s gagal: %s", job_id, error)
            job.error = "Log Perubahan gagal. Coba lagi."
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan Log Perubahan %s gagal", job_id)
            job.error = "Log Perubahan gagal. Coba lagi."
            job.status = "failed"
        finally:
            job.finished_at = time.monotonic()


def find_log_perubahan_job(job_id: str) -> Optional[LogPerubahanJob]:
    job = _log_jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _log_jobs.pop(job_id, None)
        return None
    return job
