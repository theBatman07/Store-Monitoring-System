import pandas as pd
from sqlalchemy.orm import Session
from app.models import StoreStatus, BusinessHours, Timezone
from datetime import datetime

def load_store_status(db: Session, file_path: str):
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        db_obj = StoreStatus(
            store_id=row['store_id'],
            timestamp_utc = datetime.strptime('2023-01-25 05:01:37 UTC', '%Y-%m-%d %H:%M:%S %Z'),
            status=row['status']
        )
        db.add(db_obj)
    db.commit()

def load_business_hours(db: Session, file_path: str):
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        db_obj = BusinessHours(
            store_id=row['store_id'],
            day_of_week=row['day'],
            start_time_local=row['start_time_local'],
            end_time_local=row['end_time_local']
        )
        db.add(db_obj)
    db.commit()

def load_timezones(db: Session, file_path: str):
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        db_obj = Timezone(
            store_id=row['store_id'],
            timezone_str=row['timezone_str']
        )
        db.add(db_obj)
    db.commit()