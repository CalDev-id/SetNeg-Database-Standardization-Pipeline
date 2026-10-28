"""Pekerjaan asynchronous untuk tahap Normalisasi Database."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from features.audit_db.audit import LlmRuntime
from features.audit_db.extract import ParsedDdl, parse_schema_ddl
from features.audit_db.pipeline import JOB_TTL_SECONDS, find_spreadsheet_job, record_spreadsheet_event
from features.normalization.analysis import NormalizationError, analyze_normalization
from features.normalization.output import create_normalization_excel
from shared.llm.gemini_runtime import GeminiRuntime
from shared.llm.runtime import get_runtime


logger = logging.getLogger(__name__)


@dataclass
class NormalizationJob:
    status: str
    completed_batches: int
    total_batches: int
    started_at: float
    audit_job_id: str
    source_filename: str
    table_count: int
    column_count: int
    findings: Optional[list[dict]] = None
    excel: Optional[bytes] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None


_jobs: dict[str, NormalizationJob] = {}
_tasks: set[asyncio.Task] = set()


def get_normalization_runtime(model: str) -> LlmRuntime:
    runtime = get_runtime(model)
    runtime.max_attempts = 1
    if isinstance(runtime, GeminiRuntime):
        runtime.models = (runtime.model,)
    return runtime


async def start_normalization_job(
    source_ddl: bytes, source_filename: str, audit_job_id: str,
    runtime: LlmRuntime, semaphore: asyncio.Semaphore,
) -> str:
    parsed_ddl = await asyncio.to_thread(parse_schema_ddl, source_ddl)
    for old_id, job in list(_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _jobs[old_id]
    job_id = uuid4().hex
    _jobs[job_id] = NormalizationJob(
        "queued", 0, 1, time.monotonic(),
        audit_job_id, source_filename, len(parsed_ddl.tables), parsed_ddl.column_count,
    )
    audit_job = find_spreadsheet_job(audit_job_id)
    kind = "retry" if audit_job and audit_job.normalization_job_id else "queued"
    label = "Normalisasi dicoba lagi" if kind == "retry" else "Normalisasi menunggu giliran"
    record_spreadsheet_event(audit_job_id, "normalization", kind, f"{label} · seluruh skema, 1 request.")
    task = asyncio.create_task(_run_job(job_id, parsed_ddl, runtime, semaphore))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_job(
    job_id: str, parsed_ddl: ParsedDdl, runtime: LlmRuntime, semaphore: asyncio.Semaphore,
) -> None:
    job = _jobs[job_id]
    async with semaphore:
        job.status = "running"
        record_spreadsheet_event(job.audit_job_id, "normalization", "started", "Normalisasi seluruh skema dimulai.")

        def batch_complete() -> None:
            job.completed_batches += 1

        try:
            job.findings = await analyze_normalization(parsed_ddl, runtime, batch_complete)
            job.excel = await asyncio.to_thread(create_normalization_excel, job.findings)
            job.status = "completed"
            duration = int(time.monotonic() - job.started_at)
            record_spreadsheet_event(job.audit_job_id, "normalization", "completed",
                                     f"Normalisasi selesai dalam {duration // 60:02d}:{duration % 60:02d} · {len(job.findings)} temuan.")
        except NormalizationError as error:
            job.error = str(error)
            job.status = "failed"
            record_spreadsheet_event(job.audit_job_id, "normalization", "failed", f"Normalisasi gagal: {error}")
        except Exception:
            logger.exception("Pekerjaan normalisasi %s gagal", job_id)
            job.error = "Normalisasi gagal diproses. Periksa log server."
            job.status = "failed"
            record_spreadsheet_event(job.audit_job_id, "normalization", "failed", job.error)
        finally:
            job.finished_at = time.monotonic()


def find_normalization_job(job_id: str) -> Optional[NormalizationJob]:
    job = _jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _jobs.pop(job_id, None)
        return None
    return job
