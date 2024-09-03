from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum

class StoreStatus(Base):
    __tablename__ = "store_status"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(BigInteger, index=True)  # Changed to BigInteger
    timestamp_utc = Column(DateTime)
    status = Column(String)

class BusinessHours(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(BigInteger, index=True)  # Changed to BigInteger
    day_of_week = Column(Integer)
    start_time_local = Column(String)
    end_time_local = Column(String)

class Timezone(Base):
    __tablename__ = "timezone"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(BigInteger, index=True)  # Changed to BigInteger
    timezone_str = Column(String)

class ReportStatus(enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID, primary_key=True, index=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.RUNNING)
    created_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    file_path = Column(String, nullable=True)
