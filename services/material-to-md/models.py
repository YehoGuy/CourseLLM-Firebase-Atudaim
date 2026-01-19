import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text

from db import Base


class JobStatus(str, enum.Enum):
    queued = "QUEUED"
    processing = "PROCESSING"
    completed = "COMPLETED"
    failed = "FAILED"


class ConversionJob(Base):
    __tablename__ = "conversion_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    source_path = Column(String, unique=True, nullable=False, index=True)
    file_hash = Column(String, nullable=False, index=True)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.queued)
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_deleted = Column(Boolean, default=False, nullable=False)
    processed_path = Column(String)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
