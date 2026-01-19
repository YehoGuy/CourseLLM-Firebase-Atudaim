"""Job management layer orchestrating ingestion, retries, and worker execution.

This module owns the JobManager that:

  * wires the incoming storage directory into the queued pipeline via enqueue_ingest/trigger_scan
  * maintains worker threads that pull jobs from an in-memory queue and run conversion tasks
  * runs a periodic scheduler thread (when enabled) that calls trigger_scan() every polling_interval seconds
  * handles retry/backoff logic, dead-letter moves, and journaling/administrative lookups via SQLAlchemy

All of those responsibilities live inside the JobManager class and its helper methods."""

import hashlib
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from queue import Queue, Empty
from typing import Callable, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from Converter import ConversionError, ConvertedDocument, convert_to_markdown
from db import get_session_factory, init_db
from models import ConversionJob, JobStatus
from settings import Settings, get_settings
from storage import LocalStorageBackend


class JobManager:
    """
    Lightweight in-process job manager with a worker pool and retry/backoff support.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        converter: Callable[[bytes, str], ConvertedDocument] = convert_to_markdown,
    ):
        """Instantiate the manager with configuration, storage backend, and converter callable."""
        self.settings = settings or get_settings()
        self.converter = converter
        self.storage = LocalStorageBackend(self.settings)
        self.session_factory = get_session_factory(self.settings)
        self.queue: Queue[str] = Queue()
        self._stop_event = threading.Event()
        self._workers: list[threading.Thread] = []
        self._scheduler_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Initialize storage, database tables, and start worker/scheduler threads."""
        init_db(self.settings)
        self.storage.ensure_dirs()
        self._stop_event.clear()
        self._recover_inflight_jobs()
        for _ in range(self.settings.max_concurrent_jobs):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)
        if self.settings.enable_scheduler:
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._scheduler_thread.start()

    def stop(self) -> None:
        """Signal workers to stop and join running threads."""
        self._stop_event.set()
        for worker in self._workers:
            worker.join(timeout=1)
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=1)

    @contextmanager
    def session(self) -> Session:
        """Context manager providing a database session with commit/rollback handling."""
        db = self.session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def enqueue_ingest(self, source_path: str) -> ConversionJob:
        """Create or reset a job for the given source path and queue it for processing."""
        file_bytes = self.storage.read_source(source_path)
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        processed_missing = not self.storage.processed_exists(source_path)
        with self.session() as db:
            job = db.execute(
                select(ConversionJob).where(ConversionJob.source_path == source_path)
            ).scalar_one_or_none()
            if job:
                if (
                    job.file_hash == file_hash
                    and job.status == JobStatus.completed
                    and not job.is_deleted
                    and not processed_missing
                ):
                    job.touch()
                    db.add(job)
                    return job
                job.file_hash = file_hash
                job.status = JobStatus.queued
                job.retry_count = 0
                job.error_message = None
                job.is_deleted = False
                job.touch()
            else:
                job = ConversionJob(
                    source_path=source_path,
                    file_hash=file_hash,
                    status=JobStatus.queued,
                    retry_count=0,
                    is_deleted=False,
                )
                db.add(job)

        self.queue.put(job.id)
        return job

    def trigger_scan(self) -> int:
        """Scan the incoming directory and enqueue any discovered files."""
        new_jobs = 0
        for source_path in self.storage.list_incoming_files():
            try:
                job = self.enqueue_ingest(source_path)
                if job.status == JobStatus.queued:
                    new_jobs += 1
            except FileNotFoundError:
                continue
        self._mark_missing_as_deleted()
        return new_jobs

    def get_stats(self) -> dict:
        """Return counts of jobs grouped by status."""
        with self.session() as db:
            counts = (
                db.query(ConversionJob.status, func.count(ConversionJob.id))
                .group_by(ConversionJob.status)
                .all()
            )
            result = {status.value: count for status, count in counts}
            for status in JobStatus:
                result.setdefault(status.value, 0)
            return result

    def get_job(self, job_id: str) -> ConversionJob:
        """Fetch a single job by id, raising if it does not exist."""
        with self.session() as db:
            job = db.get(ConversionJob, job_id)
            if not job:
                raise NoResultFound(job_id)
            db.expunge(job)
            return job

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[ConversionJob]:
        """List jobs with optional status and date filters, ordered by update time."""
        with self.session() as db:
            query = select(ConversionJob)
            if status:
                query = query.where(ConversionJob.status == status)
            if start:
                query = query.where(ConversionJob.updated_at >= start)
            if end:
                query = query.where(ConversionJob.updated_at <= end)
            rows = db.execute(query.order_by(ConversionJob.updated_at.desc())).scalars().all()
            for row in rows:
                db.expunge(row)
            return rows

    def get_journal_since(self, since: datetime) -> list[ConversionJob]:
        """Return all jobs updated after the given timestamp for journaling."""
        with self.session() as db:
            rows = (
                db.execute(
                    select(ConversionJob).where(ConversionJob.updated_at > since).order_by(ConversionJob.updated_at)
                )
                .scalars()
                .all()
            )
            for row in rows:
                db.expunge(row)
            return rows

    def _recover_inflight_jobs(self) -> None:
        """Requeue any jobs that were queued or processing before a restart."""
        with self.session() as db:
            inflight = db.execute(
                select(ConversionJob).where(ConversionJob.status.in_([JobStatus.queued, JobStatus.processing]))
            ).scalars()
            for job in inflight:
                job.status = JobStatus.queued
                job.touch()
                db.add(job)
                self.queue.put(job.id)

    def _worker_loop(self) -> None:
        """Worker loop that pulls job ids from the queue and processes them."""
        while not self._stop_event.is_set():
            try:
                job_id = self.queue.get(timeout=1)
            except Empty:
                continue
            try:
                self._process_job(job_id)
            finally:
                self.queue.task_done()

    def _scheduler_loop(self) -> None:
        """Periodic scheduler that triggers scans based on the configured interval."""
        while not self._stop_event.is_set():
            self.trigger_scan()
            self._stop_event.wait(timeout=self.settings.polling_interval)

    def _process_job(self, job_id: str) -> None:
        """Execute conversion for a single job, handling retries and failure bookkeeping."""
        with self.session() as db:
            job = db.get(ConversionJob, job_id)
            if not job:
                return
            try:
                job.status = JobStatus.processing
                job.touch()
                db.add(job)
                db.flush()

                file_bytes = self.storage.read_source(job.source_path)
                result = self.converter(file_bytes, source_filename(job.source_path))
                output_path = self.storage.write_processed(job.source_path, result.markdown, result.assets)

                job.status = JobStatus.completed
                job.error_message = None
                job.processed_path = output_path
                job.touch()
                db.add(job)
            except (ConversionError, FileNotFoundError, Exception) as exc:
                job.retry_count = (job.retry_count or 0) + 1
                job.error_message = str(exc)
                if job.retry_count <= self.settings.max_retries:
                    job.status = JobStatus.queued
                    delay = self.settings.retry_initial_delay * (
                        self.settings.retry_backoff_factor ** (job.retry_count - 1)
                    )
                    self._schedule_retry(job.id, delay)
                else:
                    job.status = JobStatus.failed
                    self.storage.move_to_failed(job.source_path)
                job.touch()
                db.add(job)

    def _schedule_retry(self, job_id: str, delay: float) -> None:
        """Schedule a retry for a job after the provided delay."""
        def requeue() -> None:
            self.queue.put(job_id)

        timer = threading.Timer(delay, requeue)
        timer.daemon = True
        timer.start()

    def _mark_missing_as_deleted(self) -> None:
        """Mark jobs as deleted if their source file is no longer present."""
        with self.session() as db:
            jobs = db.execute(select(ConversionJob)).scalars().all()
            for job in jobs:
                if not self.storage.source_exists(job.source_path) and not job.is_deleted:
                    job.is_deleted = True
                    job.touch()
                    db.add(job)


def source_filename(path: str) -> str:
    """Return only the filename component from a path string."""
    return str(path).split("/")[-1]
