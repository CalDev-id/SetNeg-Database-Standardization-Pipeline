"""Orkestrasi proses dan pekerjaan asynchronous audit database."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional, Union
from uuid import uuid4

from features.audit_db.audit import AuditError, LlmRuntime, audit_ddl, buat_batch_audit
from features.audit_db.audit_output import buat_excel_temuan, buat_respons_audit
from features.audit_db.extract import ParsedDdl, parse_schema_ddl


async def process_schema_audit(
    sql_input: Union[bytes, ParsedDdl], output: str,
    on_batch_complete: Optional[Callable[[], None]] = None,
    runtime: Optional[LlmRuntime] = None,
):
    # 1. Extract SQL. Job Excel sudah divalidasi saat upload.
    if isinstance(sql_input, ParsedDdl):
        parsed_ddl = sql_input
    else:
        parsed_ddl = await asyncio.to_thread(parse_schema_ddl, sql_input)

    # 2. Audit tabel dan kolom per batch.
    temuan = await audit_ddl(parsed_ddl, runtime=runtime, on_batch_complete=on_batch_complete)

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
    result: Optional[bytes] = None
    audit_result: Optional[dict] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None


_jobs: dict[str, SpreadsheetJob] = {}
_tasks: set[asyncio.Task] = set()


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
    )
    task = asyncio.create_task(_run_job(job_id, parsed_ddl, semaphore, runtime))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_job(
    job_id: str, parsed_ddl: ParsedDdl, semaphore: asyncio.Semaphore,
    runtime: LlmRuntime,
) -> None:
    job = _jobs[job_id]
    async with semaphore:
        job.status = "running"

        def batch_complete() -> None:
            job.completed_batches += 1

        try:
            job.result, job.audit_result = await process_schema_audit(
                parsed_ddl, "both", on_batch_complete=batch_complete, runtime=runtime,
            )
            job.status = "completed"
        except AuditError as error:
            job.error = str(error)
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan spreadsheet %s gagal", job_id)
            job.error = "Proses gagal. Periksa log server."
            job.status = "failed"
        finally:
            job.finished_at = time.monotonic()


def find_spreadsheet_job(job_id: str) -> Optional[SpreadsheetJob]:
    job = _jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _jobs.pop(job_id, None)
        return None
    return job
