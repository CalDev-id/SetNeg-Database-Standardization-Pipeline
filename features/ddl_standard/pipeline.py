"""Pekerjaan asynchronous untuk pembuatan DDL Standar."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from features.audit_db.audit import LlmRuntime
from features.audit_db.pipeline import JOB_TTL_SECONDS
from features.ddl_standard.ddl_standard import DdlStandardError, build_ddl_standard
from shared.llm.runtime import get_runtime


logger = logging.getLogger(__name__)


@dataclass
class DdlStandardJob:
    status: str
    completed_objects: int
    total_objects: int
    started_at: float
    audit_job_id: str
    result: Optional[dict[str, str]] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None


_jobs: dict[str, DdlStandardJob] = {}
_tasks: set[asyncio.Task] = set()


async def start_ddl_standard_job(
    source_ddl: bytes, old_dictionary: dict[str, dict], new_dictionary: dict[str, dict],
    model: str, semaphore: asyncio.Semaphore, audit_job_id: str,
) -> str:
    runtime = get_runtime(model)
    for old_id, job in list(_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _jobs[old_id]
    job_id = uuid4().hex
    _jobs[job_id] = DdlStandardJob("queued", 0, len(new_dictionary), time.monotonic(), audit_job_id)
    task = asyncio.create_task(_run_job(
        job_id, source_ddl, old_dictionary, new_dictionary, runtime, semaphore,
    ))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_job(
    job_id: str, source_ddl: bytes, old_dictionary: dict[str, dict], new_dictionary: dict[str, dict],
    runtime: LlmRuntime, semaphore: asyncio.Semaphore,
) -> None:
    job = _jobs[job_id]
    async with semaphore:
        job.status = "running"

        def object_complete() -> None:
            job.completed_objects += 1

        try:
            job.result = await build_ddl_standard(
                source_ddl, old_dictionary, new_dictionary, runtime, object_complete,
            )
            job.status = "completed"
        except DdlStandardError as error:
            job.error = str(error)
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan DDL Standar %s gagal", job_id)
            job.error = "DDL Standar gagal diproses. Periksa log server."
            job.status = "failed"
        finally:
            job.finished_at = time.monotonic()


def find_ddl_standard_job(job_id: str) -> Optional[DdlStandardJob]:
    job = _jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _jobs.pop(job_id, None)
        return None
    return job
