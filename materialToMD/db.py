"""Database utilities for engine/session creation and metadata initialization."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from settings import Settings, get_settings

import os
from typing import Any, Dict, Optional

from firebase_setup import firebase_app 
from google.cloud import firestore

_project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT")
_db = firestore.Client(project=_project_id)

def get_db() -> firestore.Client:
    """Return the shared Firestore client."""
    return _db

def save_job(job_id: str, data: Dict[str, Any]) -> None:
    """Create or update a job document."""
    get_db().collection("conversion_jobs").document(job_id).set(data)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a job document; return None if missing."""
    doc = get_db().collection("conversion_jobs").document(job_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()

def list_jobs_for_user(user_id: str) -> list[Dict[str, Any]]:
    """Example query: all jobs for a specific user."""
    docs = (
        get_db()
        .collection("conversion_jobs")
        .where("user_id", "==", user_id)
        .stream()
    )
    return [d.to_dict() | {"id": d.id} for d in docs]

Base = declarative_base()

_engine_cache: dict[str, Engine] = {}
_session_cache: dict[str, sessionmaker] = {}


def _connect_args(db_url: str) -> dict:
    """Return driver-specific connect arguments based on the database URL."""
    return {"check_same_thread": False} if db_url.startswith("sqlite") else {}


def get_engine(settings: Optional[Settings] = None) -> Engine:
    """Create or fetch a cached SQLAlchemy engine for the configured database."""
    settings = settings or get_settings()
    key = settings.db_url
    if key not in _engine_cache:
        _engine_cache[key] = create_engine(settings.db_url, connect_args=_connect_args(settings.db_url), future=True)
    return _engine_cache[key]


def get_session_factory(settings: Optional[Settings] = None) -> sessionmaker:
    """Return a cached sessionmaker bound to the configured engine."""
    settings = settings or get_settings()
    key = settings.db_url
    if key not in _session_cache:
        _session_cache[key] = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine(settings), future=True, expire_on_commit=False
        )
    return _session_cache[key]


def init_db(settings: Optional[Settings] = None) -> None:
    """Create all known database tables if they do not yet exist."""
    # Imported lazily to avoid circular references
    from models import ConversionJob  # noqa: F401

    Base.metadata.create_all(bind=get_engine(settings))
