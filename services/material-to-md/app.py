import os
import time
import platform
import psutil
from datetime import datetime, timezone
from typing import List, Optional
from contextlib import asynccontextmanager
from uuid import uuid4

# --- CRITICAL FIX: FORCE EMULATOR USAGE ---
# We set these BEFORE importing 'db' or 'jobs' so they connect to localhost
# instead of trying to authenticate with real Google Cloud.
os.environ["GCLOUD_PROJECT"] = "demo-project"
os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "127.0.0.1:9199"

from fastapi import FastAPI, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
from google.cloud import storage as gcs
from google.auth.credentials import AnonymousCredentials

# Local Imports (These will now work because of the env vars above)
from Converter import ConversionError, ConvertedDocument, convert_to_markdown
from jobs import JobManager
from models import JobStatus
from settings import Settings, get_settings
from db import save_job, get_job, list_jobs_for_user, get_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---

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

# --- APP FACTORY & LIFECYCLE ---

def create_app(settings: Optional[Settings] = None, manager: Optional[JobManager] = None) -> FastAPI:
    settings = settings or get_settings()
    manager = manager or JobManager(settings=settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        manager.start()
        app.state.job_manager = manager
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
        return request.app.state.job_manager

    # --- ENDPOINTS ---

    @app.post("/convert", response_model=ConvertResponse)
    async def convert(file: UploadFile = File(...)) -> ConvertResponse:
        """
        Synchronous conversion endpoint used for direct conversion without queuing.
        (Logic Preserved: Converts -> Uploads to Emulator Storage -> Saves to Emulator Firestore)
        """
        try:
            content = await file.read()
            # 1. Convert
            result: ConvertedDocument = convert_to_markdown(content, file.filename)
        except ConversionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        # 2. Upload Markdown to Firebase Storage EMULATOR
        storage_host = os.getenv("FIREBASE_STORAGE_EMULATOR_HOST", "127.0.0.1:9199")
        project_id = os.getenv("GCLOUD_PROJECT", "demo-project")
        bucket_name = f"{project_id}.appspot.com"

        # Client uses AnonymousCredentials -> Connects to Emulator
        client = gcs.Client(
            project=project_id,
            credentials=AnonymousCredentials(),
            client_options={"api_endpoint": f"http://{storage_host}"}
        )

        bucket = client.bucket(bucket_name)
        job_id = f"convert-{uuid4().hex}"
        md_path = f"converted/{job_id}.md"

        try:
            blob = bucket.blob(md_path)
            blob.upload_from_string(
                result.markdown,
                content_type="text/markdown",
            )
            # Create Emulator Link
            safe_path = md_path.replace("/", "%2F")
            output_md_url = f"http://{storage_host}/v0/b/{bucket_name}/o/{safe_path}?alt=media"
        except Exception as e:
            print(f"Storage Warning: Could not upload to emulator ({e}). Proceeding...")
            output_md_url = ""

        # 3. Save metadata into Firestore (Emulator)
        try:
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
        except Exception as e:
            print(f"Firestore Warning: Could not save to DB ({e}). Ensure emulators are running.")

        # 4. Return Response
        assets = [
            AssetResponse(path=asset.path, content_type=asset.content_type, data_base64=asset.data_base64)
            for asset in result.assets
        ]
        return ConvertResponse(markdown=result.markdown, assets=assets)

    # --- SYSTEM HEALTH DASHBOARD ---
    @app.get("/system-stats")
    def get_system_stats():
        return {
            "status": "Healthy",
            "uptime": time.time(),
            "cpu": {
                "usage": psutil.cpu_percent(interval=None),
                "cores": psutil.cpu_count(logical=True),
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "used": round(psutil.virtual_memory().used / (1024**3), 2),
                "total": round(psutil.virtual_memory().total / (1024**3), 2),
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent,
                "free": round(psutil.disk_usage('/').free / (1024**3), 2),
            },
            "system": {
                "node": platform.node(),
                "os": platform.system(),
            }
        }

    # --- JOB MANAGEMENT ENDPOINTS ---
    @app.post("/v1/ingest", response_model=JobResponse, status_code=202)
    def ingest(payload: IngestRequest, manager: JobManager = Depends(get_manager)) -> JobResponse:
        try:
            job = manager.enqueue_ingest(payload.source_path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _job_to_response(job)

    @app.post("/v1/trigger-scan", response_model=TriggerScanResponse)
    def trigger_scan(manager: JobManager = Depends(get_manager)) -> TriggerScanResponse:
        queued = manager.trigger_scan()
        return TriggerScanResponse(queued=queued)

    @app.get("/v1/admin/stats", response_model=StatsResponse)
    def admin_stats(manager: JobManager = Depends(get_manager)) -> StatsResponse:
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
        jobs = manager.list_jobs(status=status, start=start, end=end)
        return [_job_to_response(job) for job in jobs]

    @app.get("/v1/admin/jobs/{job_id}", response_model=JobResponse)
    def get_job(job_id: str, manager: JobManager = Depends(get_manager)) -> JobResponse:
        try:
            job = manager.get_job(job_id)
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Job not found")
        return _job_to_response(job)

    @app.get("/v1/journal/sync", response_model=List[JobResponse])
    def journal_sync(
        since: datetime = Query(...),
        manager: JobManager = Depends(get_manager),
    ) -> List[JobResponse]:
        jobs = manager.get_journal_since(since)
        return [_job_to_response(job) for job in jobs]

    return app

def _job_to_response(job) -> JobResponse:
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

# Initialize
app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
