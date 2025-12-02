import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient

from Converter import ConversionError, ConvertedDocument
from app import create_app
from jobs import JobManager
from models import JobStatus
from settings import Settings


def _settings(tmp_path: Path, **overrides) -> Settings:
    return Settings(
        db_url=f"sqlite:///{tmp_path}/fns.db",
        storage_root=tmp_path / "storage",
        max_concurrent_jobs=2,
        max_retries=overrides.get("max_retries", 2),
        retry_initial_delay=0.05,
        retry_backoff_factor=1.0,
        polling_interval=1,
        enable_scheduler=False,
    )


def _wait_for_status(manager: JobManager, job_id: str, desired: JobStatus, timeout: float = 5.0):
    deadline = time.time() + timeout
    last_job = None
    while time.time() < deadline:
        last_job = manager.get_job(job_id)
        if last_job.status == desired:
            return last_job
        time.sleep(0.05)
    assert last_job is not None
    raise AssertionError(f"Job {job_id} did not reach {desired} (last={last_job.status})")


def _write_sample_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _simple_converter() -> Callable:
    def converter(file_bytes: bytes, filename: str) -> ConvertedDocument:
        text = file_bytes.decode("utf-8", errors="ignore")
        return ConvertedDocument(markdown=text, assets=[])

    return converter


def test_trigger_scan_reprocesses_missing_output(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    manager = JobManager(settings=settings, converter=_simple_converter())
    app = create_app(settings=settings, manager=manager)

    incoming_file = settings.storage_root / settings.incoming_dir / "missing.pdf"
    _write_sample_file(incoming_file, "content")

    with TestClient(app) as client:
        # First ingest to create job and processed file
        client.post("/v1/ingest", json={"source_path": "missing.pdf"})
        job = _wait_for_status(manager, manager.list_jobs()[0].id, JobStatus.completed)
        processed = settings.storage_root / settings.processed_dir / "missing.md"
        assert processed.exists()

        # Remove processed output to simulate missing md file
        processed.unlink()
        assert not processed.exists()

        # Trigger scan should re-enqueue and recreate processed file
        client.post("/v1/trigger-scan")
        job_after = _wait_for_status(manager, job.id, JobStatus.completed)
        assert job_after.updated_at >= job.updated_at
        assert processed.exists()


def test_ingest_process_and_stats(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    manager = JobManager(settings=settings, converter=_simple_converter())
    app = create_app(settings=settings, manager=manager)
    incoming_file = settings.storage_root / settings.incoming_dir / "doc1.txt"
    _write_sample_file(incoming_file, "hello world")

    with TestClient(app) as client:
        resp = client.post("/v1/ingest", json={"source_path": "doc1.txt"})
        assert resp.status_code == 202
        job_id = resp.json()["id"]

        job = _wait_for_status(manager, job_id, JobStatus.completed)
        processed = settings.storage_root / settings.processed_dir / "doc1.md"
        assert processed.exists()
        assert "hello world" in processed.read_text(encoding="utf-8")

        stats = client.get("/v1/admin/stats").json()
        assert stats["completed"] >= 1
        assert stats["failed"] == 0


def test_retry_then_success(tmp_path: Path) -> None:
    attempts = {"count": 0}

    def flaky(file_bytes: bytes, filename: str) -> ConvertedDocument:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ConversionError("boom")
        return ConvertedDocument(markdown="ok", assets=[])

    settings = _settings(tmp_path, max_retries=2)
    manager = JobManager(settings=settings, converter=flaky)
    app = create_app(settings=settings, manager=manager)
    incoming_file = settings.storage_root / settings.incoming_dir / "flaky.txt"
    _write_sample_file(incoming_file, "retry me")

    with TestClient(app) as client:
        resp = client.post("/v1/ingest", json={"source_path": "flaky.txt"})
        assert resp.status_code == 202
        job_id = resp.json()["id"]
        job = _wait_for_status(manager, job_id, JobStatus.completed)
        assert attempts["count"] >= 2
        assert job.retry_count == 1


def test_dead_letter_on_exceeded_retries(tmp_path: Path) -> None:
    def always_fail(file_bytes: bytes, filename: str) -> ConvertedDocument:
        raise ConversionError("never works")

    settings = _settings(tmp_path, max_retries=1)
    manager = JobManager(settings=settings, converter=always_fail)
    app = create_app(settings=settings, manager=manager)
    incoming_file = settings.storage_root / settings.incoming_dir / "bad.txt"
    _write_sample_file(incoming_file, "data")

    with TestClient(app) as client:
        resp = client.post("/v1/ingest", json={"source_path": "bad.txt"})
        assert resp.status_code == 202
        job_id = resp.json()["id"]
        job = _wait_for_status(manager, job_id, JobStatus.failed)
        assert job.retry_count == 2  # initial attempt + retry
        failed_path = settings.storage_root / settings.failed_dir / "bad.txt"
        assert failed_path.exists()


def test_trigger_scan_and_journal(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    manager = JobManager(settings=settings, converter=_simple_converter())
    app = create_app(settings=settings, manager=manager)
    incoming_file = settings.storage_root / settings.incoming_dir / "scan.txt"
    _write_sample_file(incoming_file, "scan content")

    with TestClient(app) as client:
        client.post("/v1/trigger-scan")
        job = None
        # wait for scan to enqueue and process
        deadline = time.time() + 5
        while time.time() < deadline:
            jobs = client.get("/v1/admin/jobs").json()
            if jobs:
                job = jobs[0]
                if job["status"] == JobStatus.completed.value:
                    break
            time.sleep(0.05)
        assert job is not None
        job_id = job["id"]

        since = datetime.now(timezone.utc) - timedelta(minutes=5)
        journal = client.get("/v1/journal/sync", params={"since": since.isoformat()}).json()
        assert any(entry["id"] == job_id for entry in journal)

        # mark as deleted by removing source and scanning again
        (settings.storage_root / settings.incoming_dir / "scan.txt").unlink()
        client.post("/v1/trigger-scan")
        time.sleep(0.2)
        journal_after_delete = client.get("/v1/journal/sync", params={"since": since.isoformat()}).json()
        deleted_entry = next(e for e in journal_after_delete if e["id"] == job_id)
        assert deleted_entry["is_deleted"] is True
