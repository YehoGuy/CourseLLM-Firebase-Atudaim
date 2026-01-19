import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    db_url: str = os.environ.get("DB_URL", "sqlite:///./fns.db")
    storage_root: Path = Path(os.environ.get("STORAGE_ROOT", "./storage")).resolve()
    incoming_dir: str = os.environ.get("INCOMING_DIR", "incoming")
    processed_dir: str = os.environ.get("PROCESSED_DIR", "processed")
    failed_dir: str = os.environ.get("FAILED_DIR", "failed_conversions")
    max_concurrent_jobs: int = _int("MAX_CONCURRENT_JOBS", 4)
    max_retries: int = _int("MAX_RETRIES", 3)
    retry_backoff_factor: float = _float("RETRY_BACKOFF_FACTOR", 2.0)
    retry_initial_delay: float = _float("RETRY_INITIAL_DELAY", 1.0)
    polling_interval: int = _int("POLLING_INTERVAL", 300)
    journaling_page_size: int = _int("JOURNAL_PAGE_SIZE", 200)
    enable_scheduler: bool = _bool("ENABLE_SCHEDULER", True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
