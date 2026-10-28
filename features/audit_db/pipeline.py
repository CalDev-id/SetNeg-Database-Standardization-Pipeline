"""Orkestrasi proses dan pekerjaan asynchronous audit database."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Union
from uuid import uuid4

from features.audit_db.audit import AuditError, LlmRuntime, Temuan, audit_ddl, buat_batch_audit
from features.audit_db.audit_output import buat_excel_temuan, buat_respons_audit
from features.audit_db.extract import ParsedDdl, parse_schema_ddl
from shared.llm.openai_runtime import OpenAIEmptyResponseError, OpenAIRuntime


async def process_schema_audit(
    sql_input: Union[bytes, ParsedDdl], output: str,
    on_batch_complete: Optional[Callable[[], None]] = None,
    runtime: Optional[LlmRuntime] = None,
    on_event: Optional[Callable[[str, str], None]] = None,
    completed_batches: int = 0,
    previous_findings: Optional[list[Temuan]] = None,
    on_batch_result: Optional[Callable[[list[Temuan]], None]] = None,
):
    # 1. Extract SQL. Job Excel sudah divalidasi saat upload.
    if isinstance(sql_input, ParsedDdl):
        parsed_ddl = sql_input
    else:
        parsed_ddl = await asyncio.to_thread(parse_schema_ddl, sql_input)

    # 2. Audit tabel dan kolom per batch.
    temuan = await audit_ddl(parsed_ddl, runtime=runtime, on_batch_complete=on_batch_complete,
                            on_event=on_event, completed_batches=completed_batches,
                            previous_findings=previous_findings, on_batch_result=on_batch_result)

    # 3. Buat output sesuai endpoint.
    if output == "json":
        return buat_respons_audit(parsed_ddl, temuan)
    if output in {"excel", "both"}:
        spreadsheet = await asyncio.to_thread(
            buat_excel_temuan, parsed_ddl.database_name or "-", temuan,
        )
        if output == "both":
            return spreadsheet, buat_respons_audit(parsed_ddl, temuan)
        return spreadsheet
    raise ValueError("Format output tidak dikenal.")


JOB_TTL_SECONDS = 3600
logger = logging.getLogger(__name__)


@dataclass
class SpreadsheetJob:
    status: str
    completed_batches: int
    total_batches: int
    started_at: float
    source_ddl: bytes
    source_filename: str
    normalization_job_id: Optional[str] = None
    normalization_error: Optional[str] = None
    result: Optional[bytes] = None
    audit_result: Optional[dict] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None
    process_events: Optional[list[dict]] = None
    parsed_ddl: Optional[ParsedDdl] = None
    runtime: Optional[LlmRuntime] = None
    partial_findings: list[Temuan] = field(default_factory=list)
    output_limit_hit: bool = False


_jobs: dict[str, SpreadsheetJob] = {}
_tasks: set[asyncio.Task] = set()


def record_spreadsheet_event(job_id: str, stage: str, kind: str, message: str) -> None:
    job = _jobs.get(job_id)
    if job is None:
        return
    if job.process_events is None:
        job.process_events = []
    job.process_events.append({
        "stage": stage, "kind": kind, "message": message[:240],
        "elapsed_seconds": max(0, int(time.monotonic() - job.started_at)),
    })
    if len(job.process_events) > 120:
        del job.process_events[:-120]


async def start_spreadsheet_job(
    content: bytes, filename: str, semaphore: asyncio.Semaphore, runtime: LlmRuntime,
) -> str:
    # Validasi SQL sebelum membuat job.
    parsed_ddl = await asyncio.to_thread(parse_schema_ddl, content)
    for old_id, job in list(_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _jobs[old_id]
    job_id = uuid4().hex
    batch_size = max(1, int(getattr(runtime, "batch_size", 50)))
    total_batches = len(buat_batch_audit(
        parsed_ddl, batch_size, getattr(runtime, "max_tables_per_batch", None),
    ))
    _jobs[job_id] = SpreadsheetJob(
        status="queued",
        completed_batches=0,
        total_batches=total_batches,
        started_at=time.monotonic(),
        source_ddl=content,
        source_filename=filename,
        parsed_ddl=parsed_ddl,
        runtime=runtime,
    )
    record_spreadsheet_event(job_id, "audit", "queued", f"Audit menunggu giliran · {total_batches} batch.")
    task = asyncio.create_task(_run_job(job_id, parsed_ddl, semaphore, runtime))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


def retry_spreadsheet_job(job_id: str, semaphore: asyncio.Semaphore) -> SpreadsheetJob:
    job = find_spreadsheet_job(job_id)
    if job is None:
        raise LookupError("Pekerjaan Audit tidak ditemukan atau sudah kedaluwarsa.")
    if job.status != "failed":
        raise ValueError("Hanya pekerjaan Audit yang gagal dapat dicoba lagi.")
    if job.parsed_ddl is None or job.runtime is None:
        raise ValueError("Hasil batch sebelumnya tidak tersedia; unggah ulang DDL.")
    retry_detail = "mencoba lagi"
    if job.output_limit_hit and isinstance(job.runtime, OpenAIRuntime) \
            and job.runtime.allow_reasoning_retries:
        runtime = job.runtime
        if runtime.model == "gpt-6-luna" and runtime.reasoning_effort == "low":
            runtime.reasoning_effort = "none"
            runtime.max_completion_tokens = max(runtime.max_completion_tokens, 45000)
            retry_detail = "penalaran dikurangi, batas token ditambah, mencoba lagi"
        elif runtime.model == "gpt-6-luna" and runtime.reasoning_effort == "none":
            runtime.max_completion_tokens = max(runtime.max_completion_tokens, 60000)
            retry_detail = "batas token ditambah, mencoba lagi"
        else:
            runtime.max_completion_tokens = max(runtime.max_completion_tokens, 30000)
            if runtime.model == "gpt-6-luna":
                runtime.reasoning_effort = "low"
            retry_detail = "batas token ditambah, mencoba lagi"
    job.status = "queued"
    job.error = None
    job.finished_at = None
    record_spreadsheet_event(
        job_id, "audit", "retry",
        f"Audit batch {job.completed_batches + 1}/{job.total_batches}: {retry_detail}.",
    )
    task = asyncio.create_task(_run_job(job_id, job.parsed_ddl, semaphore, job.runtime))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job


async def _run_job(
    job_id: str, parsed_ddl: ParsedDdl, semaphore: asyncio.Semaphore,
    runtime: LlmRuntime,
) -> None:
    job = _jobs[job_id]
    async with semaphore:
        job.status = "running"
        record_spreadsheet_event(job_id, "audit", "started", "Audit dimulai.")

        def batch_complete() -> None:
            job.completed_batches += 1

        def batch_result(findings: list[Temuan]) -> None:
            job.partial_findings.extend(findings)

        try:
            job.result, job.audit_result = await process_schema_audit(
                parsed_ddl, "both", on_batch_complete=batch_complete, runtime=runtime,
                on_event=lambda kind, message: record_spreadsheet_event(job_id, "audit", kind, message),
                completed_batches=job.completed_batches,
                previous_findings=job.partial_findings,
                on_batch_result=batch_result,
            )
            job.status = "completed"
            record_spreadsheet_event(job_id, "audit", "completed", "Audit selesai.")
        except AuditError as error:
            job.error = str(error)
            job.status = "failed"
            cause = error.__cause__
            job.output_limit_hit = (
                isinstance(cause, OpenAIEmptyResponseError) and cause.finish_reason == "length"
            )
            record_spreadsheet_event(job_id, "audit", "failed", f"Audit gagal: {error}")
        except Exception:
            logger.exception("Pekerjaan spreadsheet %s gagal", job_id)
            job.error = "Proses gagal. Periksa log server."
            job.status = "failed"
            record_spreadsheet_event(job_id, "audit", "failed", job.error)
        finally:
            job.finished_at = time.monotonic()


def find_spreadsheet_job(job_id: str) -> Optional[SpreadsheetJob]:
    job = _jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _jobs.pop(job_id, None)
        return None
    return job
