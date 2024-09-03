from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.models import ReportStatus

class ReportResponse(BaseModel):
    report_id: str

class ReportStatusResponse(BaseModel):
    report_id: UUID
    status: ReportStatus
    created_at: datetime
    completed_at: datetime | None = None
    file_url: str | None = None