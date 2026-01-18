"""FastAPI wiring for the File Normalization Service HTTP API surface."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- IMPORT THIS

from datetime import datetime
import os
from typing import List, Optional

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound

from Converter import ConversionError, ConvertedDocument, convert_to_markdown
from jobs import JobManager
from models import JobStatus
from settings import Settings, get_settings

from db import save_job, get_job, list_jobs_for_user, get_db
from datetime import datetime, timezone
from uuid import uuid4

from google.cloud import storage as gcs           
from google.auth.credentials import AnonymousCredentials

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


def create_job_flow(job_id: str, user_id: str, payload: dict) -> None:
    save_job(job_id, {
        "user_id": user_id,
        "payload": payload,
        "status": "pending",
    })


def read_job_flow(job_id: str):
    job = get_job(job_id)
    if job is None:
        print("Job not found")
    else:
        print("Job:", job)

class AssetResponse(BaseModel):
    path: str
    content_type: str
    data_base64: str


class ConvertResponse(BaseModel):
    markdown: str
    assets: List[AssetResponse]


class IngestRequest(BaseModel):
    source_path: str


class JobResponse(BaseModel):
    id: str
    source_path: str
    status: JobStatus
    retry_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    processed_path: Optional[str]
    is_deleted: bool


class StatsResponse(BaseModel):
    queued: int
    processing: int
    completed: int
    failed: int


class TriggerScanResponse(BaseModel):
    queued: int


def create_app(settings: Optional[Settings] = None, manager: Optional[JobManager] = None) -> FastAPI:
    """Build and configure the FastAPI application with injected settings and job manager."""
    settings = settings or get_settings()
    manager = manager or JobManager(settings=settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Start and stop the job manager alongside the FastAPI lifespan."""
        manager.start()
        app.state.job_manager = manager  # type: ignore[attr-defined]
        try:
            yield
        finally:
            manager.stop()

    app = FastAPI(title="File Normalization Service", version="1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )



    def get_manager(request: Request) -> JobManager:
        return request.app.state.job_manager  # type: ignore[attr-defined]

    @app.post("/convert", response_model=ConvertResponse)
    async def convert(file: UploadFile = File(...)) -> ConvertResponse:
        """Synchronous conversion endpoint used for direct conversion without queuing."""
        try:
            content = await file.read()
            result: ConvertedDocument = convert_to_markdown(content, file.filename)
        except ConversionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        # ---------- 1) Upload Markdown to Firebase Storage EMULATOR ----------
        storage_host = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST", "127.0.0.1:9199")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT")
        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET") or f"{project_id}.appspot.com"

        # Create a storage client that talks to the emulator with anonymous creds
        client = gcs.Client(
            project=project_id,
            credentials=AnonymousCredentials(),
            client_options={"api_endpoint": f"http://{storage_host}"}
        )

        bucket = client.bucket(bucket_name)
        job_id = f"convert-{uuid4().hex}"
        md_path = f"converted/{job_id}.md"

        blob = bucket.blob(md_path)
        blob.upload_from_string(
            result.markdown,
            content_type="text/markdown",
        )

        # Build a local emulator URL for convenience
        safe_path = md_path.replace("/", "%2F")
        output_md_url = f"http://{storage_host}/v0/b/{bucket_name}/o/{safe_path}?alt=media"

        # ---------- 2) Save metadata into Firestore ----------
        db = get_db()
        db.collection("conversion_jobs").document(job_id).set({
            "job_id": job_id,
            "file_name": file.filename,
            "input_file_type": file.filename.split(".")[-1].lower(),
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "output_md_path": md_path,
            "output_md_url": output_md_url,
        })

        # ---------- 3) Original response ----------
        assets = [
            AssetResponse(path=asset.path, content_type=asset.content_type, data_base64=asset.data_base64)
            for asset in result.assets
        ]
        return ConvertResponse(markdown=result.markdown, assets=assets)

    @app.post("/v1/ingest", response_model=JobResponse, status_code=202)
    def ingest(payload: IngestRequest, manager: JobManager = Depends(get_manager)) -> JobResponse:
        """Accept an ingest request and enqueue the source file for async processing."""
        try:
            job = manager.enqueue_ingest(payload.source_path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _job_to_response(job)

    @app.post("/v1/trigger-scan", response_model=TriggerScanResponse)
    def trigger_scan(manager: JobManager = Depends(get_manager)) -> TriggerScanResponse:
        """Scan the incoming folder to enqueue any untracked files."""
        queued = manager.trigger_scan()
        return TriggerScanResponse(queued=queued)

    @app.get("/v1/admin/stats", response_model=StatsResponse)
    def admin_stats(manager: JobManager = Depends(get_manager)) -> StatsResponse:
        """Return aggregate job counts by status for observability."""
        stats = manager.get_stats()
        return StatsResponse(
            queued=stats.get(JobStatus.queued.value, 0),
            processing=stats.get(JobStatus.processing.value, 0),
            completed=stats.get(JobStatus.completed.value, 0),
            failed=stats.get(JobStatus.failed.value, 0),
        )

    @app.get("/v1/admin/jobs", response_model=List[JobResponse])
    def list_jobs(
        status: Optional[JobStatus] = Query(None),
        start: Optional[datetime] = Query(None),
        end: Optional[datetime] = Query(None),
        manager: JobManager = Depends(get_manager),
    ) -> List[JobResponse]:
        """List jobs filtered by status or time window for administrative inspection."""
        jobs = manager.list_jobs(status=status, start=start, end=end)
        return [_job_to_response(job) for job in jobs]

    @app.get("/v1/admin/jobs/{job_id}", response_model=JobResponse)
    def get_job(job_id: str, manager: JobManager = Depends(get_manager)) -> JobResponse:
        """Fetch a specific job with its current status and error details."""
        try:
            job = manager.get_job(job_id)
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Job not found")
        return _job_to_response(job)

    @app.get("/v1/journal/sync", response_model=List[JobResponse])
    def journal_sync(
        since_timestamp: datetime = Query(..., alias="since"),
        manager: JobManager = Depends(get_manager),
    ) -> List[JobResponse]:
        """Return jobs updated after the requested timestamp for downstream sync."""
        jobs = manager.get_journal_since(since_timestamp)
        return [_job_to_response(job) for job in jobs]

    return app


def _job_to_response(job) -> JobResponse:
    """Map a ConversionJob ORM instance to the JobResponse payload model."""
    return JobResponse(
        id=job.id,
        source_path=job.source_path,
        status=job.status,
        retry_count=job.retry_count,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        processed_path=job.processed_path,
        is_deleted=job.is_deleted,
    )


app = create_app()
