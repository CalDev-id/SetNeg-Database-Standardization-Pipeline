"""Pekerjaan asynchronous untuk tahapan Data Dictionary."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from features.audit_db.audit import LlmRuntime
from features.audit_db.extract import ParsedDdl, parse_schema_ddl
from features.audit_db.pipeline import JOB_TTL_SECONDS
from features.data_dictionary.dictionary_old import OldDictionaryError, build_old_dictionary, parse_existing_objects
from features.data_dictionary.dictionary_new import NewDictionaryError, build_new_dictionary, count_batches
from features.data_dictionary.log_perubahan import LogPerubahanError, build_log_perubahan, count_log_batches
from features.data_dictionary.table_classification import ClassificationError, classify_tables
from shared.llm.runtime import get_runtime


logger = logging.getLogger(__name__)


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
    source_ddl: bytes, findings: list[dict], model: str, semaphore: asyncio.Semaphore,
    audit_job_id: str,
) -> str:
    parsed_ddl = await asyncio.to_thread(parse_schema_ddl, source_ddl)
    runtime = get_runtime(model)
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
            job.error = str(error)
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan klasifikasi %s gagal", job_id)
            job.error = "Klasifikasi gagal. Periksa log server."
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
    runtime = get_runtime(model)
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
            job.error = str(error)
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan Old Dictionary %s gagal", job_id)
            job.error = "Old Dictionary gagal diproses. Periksa log server."
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
    result: Optional[dict[str, dict]] = None
    error: Optional[str] = None
    finished_at: Optional[float] = None


_new_jobs: dict[str, NewDictionaryJob] = {}


async def start_new_dictionary_job(
    source_ddl: bytes, findings: list[dict], classification: dict[str, dict],
    model: str, semaphore: asyncio.Semaphore,
    audit_job_id: str,
) -> str:
    objects = await asyncio.to_thread(parse_existing_objects, source_ddl)
    runtime = get_runtime(model)
    for old_id, job in list(_new_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _new_jobs[old_id]

    job_id = uuid4().hex
    _new_jobs[job_id] = NewDictionaryJob("queued", 0, count_batches(objects, findings), time.monotonic(), audit_job_id)
    task = asyncio.create_task(_run_new_dictionary_job(
        job_id, source_ddl, findings, classification, runtime, semaphore,
    ))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_new_dictionary_job(
    job_id: str, source_ddl: bytes, findings: list[dict], classification: dict[str, dict],
    runtime: LlmRuntime, semaphore: asyncio.Semaphore,
) -> None:
    job = _new_jobs[job_id]
    async with semaphore:
        job.status = "running"

        def batch_complete() -> None:
            job.completed_batches += 1

        try:
            job.result = await build_new_dictionary(
                source_ddl, findings, classification, runtime, batch_complete,
            )
            job.status = "completed"
        except NewDictionaryError as error:
            job.error = str(error)
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan Dictionary New %s gagal", job_id)
            job.error = "Dictionary New gagal diproses. Periksa log server."
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
) -> str:
    runtime = get_runtime(model)
    for old_id, job in list(_log_jobs.items()):
        if job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS:
            del _log_jobs[old_id]
    job_id = uuid4().hex
    _log_jobs[job_id] = LogPerubahanJob("queued", 0, count_log_batches(new_dictionary), time.monotonic())
    task = asyncio.create_task(_run_log_perubahan_job(
        job_id, old_dictionary, new_dictionary, findings, runtime, semaphore,
    ))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run_log_perubahan_job(
    job_id: str, old_dictionary: dict[str, dict], new_dictionary: dict[str, dict],
    findings: list[dict], runtime: LlmRuntime, semaphore: asyncio.Semaphore,
) -> None:
    job = _log_jobs[job_id]
    async with semaphore:
        job.status = "running"

        def batch_complete() -> None:
            job.completed_batches += 1

        try:
            job.result = await build_log_perubahan(
                old_dictionary, new_dictionary, findings, runtime, batch_complete,
            )
            job.status = "completed"
        except LogPerubahanError as error:
            job.error = str(error)
            job.status = "failed"
        except Exception:
            logger.exception("Pekerjaan Log Perubahan %s gagal", job_id)
            job.error = "Log Perubahan gagal diproses. Periksa log server."
            job.status = "failed"
        finally:
            job.finished_at = time.monotonic()


def find_log_perubahan_job(job_id: str) -> Optional[LogPerubahanJob]:
    job = _log_jobs.get(job_id)
    if not job or (job.finished_at is not None and time.monotonic() - job.finished_at > JOB_TTL_SECONDS):
        _log_jobs.pop(job_id, None)
        return None
    return job
