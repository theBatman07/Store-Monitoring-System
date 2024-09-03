from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db, engine
from app.models import Base, Report, ReportStatus
from app.schemas import ReportResponse, ReportStatusResponse
from app.data_loader import load_store_status, load_business_hours, load_timezones
import uuid
from datetime import datetime, timedelta, timezone
import os
import pandas as pd
from fastapi.responses import FileResponse

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        # Load data from CSV files
        load_store_status(db, "store_status.csv")
        load_business_hours(db, "menu_hours.csv")
        load_timezones(db, "bq-results-20230125-202210-1674678181880.csv")
    finally:
        db.close()

@app.post("/trigger_report", response_model=ReportResponse)
async def trigger_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    report_id = uuid.uuid4()
    new_report = Report(id=report_id, created_at=datetime.now(timezone.utc))
    db.add(new_report)
    db.commit()
    
    background_tasks.add_task(generate_report, report_id, db)
    return {"report_id": str(report_id)}

@app.get("/get_report/{report_id}", response_model=ReportStatusResponse)
async def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    response = ReportStatusResponse(
        report_id=report.id,
        status=report.status,
        created_at=report.created_at,
        completed_at=report.completed_at,
        file_url=f"/download/{report.file_path}" if report.file_path else None
    )
    
    return response

@app.get("/download/{file_path}")
async def download_report(file_path: str):
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/csv", filename=os.path.basename(file_path))
    raise HTTPException(status_code=404, detail="File not found")

def generate_report(report_id: uuid.UUID, db: Session):
    try:
        # Fetch the data needed for report generation
        store_status = pd.read_sql_table('store_status', con=db.bind)
        business_hours = pd.read_sql_table('business_hours', con=db.bind)
        timezones = pd.read_sql_table('timezone', con=db.bind)
        
        current_timestamp = max(pd.to_datetime(store_status['timestamp']))

        report_data = []

        store_ids = store_status['store_id'].unique()
        
        for store_id in store_ids:
            # Calculate the uptime and downtime for the last hour, day, and week
            uptime_last_hour, downtime_last_hour = calculate_uptime_downtime(store_id, current_timestamp, timedelta(hours=1), store_status, business_hours)
            uptime_last_day, downtime_last_day = calculate_uptime_downtime(store_id, current_timestamp, timedelta(days=1), store_status, business_hours)
            uptime_last_week, downtime_last_week = calculate_uptime_downtime(store_id, current_timestamp, timedelta(weeks=1), store_status, business_hours)
            
            report_data.append({
                "store_id": store_id,
                "uptime_last_hour": uptime_last_hour,
                "uptime_last_day": uptime_last_day / 60,
                "uptime_last_week": uptime_last_week / 60,
                "downtime_last_hour": downtime_last_hour,
                "downtime_last_day": downtime_last_day / 60,
                "downtime_last_week": downtime_last_week / 60
            })
        
        # Save the report to a CSV file
        file_path = f"reports/{report_id}.csv"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        report_df = pd.DataFrame(report_data)
        report_df.to_csv(file_path, index=False)
        
        # Update report status in the database
        report = db.query(Report).filter(Report.id == report_id).first()
        report.status = ReportStatus.COMPLETED
        report.completed_at = datetime.utcnow()
        report.file_path = file_path
        db.commit()
    except Exception as e:
        print(f"Error generating report {report_id}: {str(e)}")
        report = db.query(Report).filter(Report.id == report_id).first()
        report.status = ReportStatus.FAILED
        db.commit()

def calculate_uptime_downtime(store_id, current_timestamp, period_duration, store_status, business_hours):
    """Calculate uptime and downtime for a specific period."""
    # Define the time range
    end_time = current_timestamp
    start_time = end_time - period_duration
    
    # Get the business hours for the store and date
    business_hours_store = business_hours[business_hours['store_id'] == store_id]
    
    uptime = timedelta(0)
    downtime = timedelta(0)
    
    for _, hours in business_hours_store.iterrows():
        # For each business hours entry, check if it overlaps with the period
        business_start = pd.to_datetime(hours['start_time']).replace(year=start_time.year, month=start_time.month, day=start_time.day)
        business_end = pd.to_datetime(hours['end_time']).replace(year=start_time.year, month=start_time.month, day=start_time.day)
        
        if business_end < start_time or business_start > end_time:
            continue
        
        # Clip business hours to the period duration
        period_start = max(start_time, business_start)
        period_end = min(end_time, business_end)
        
        # Filter status data for this period
        status_period = store_status[(store_status['store_id'] == store_id) & 
                                     (store_status['timestamp'] >= period_start) & 
                                     (store_status['timestamp'] <= period_end)]
        
        if not status_period.empty:
            status_period = status_period.sort_values(by='timestamp')
            previous_time = period_start
            previous_status = None
            
            for _, row in status_period.iterrows():
                current_time = pd.to_datetime(row['timestamp'])
                current_status = row['status']
                
                if previous_status is not None:
                    duration = current_time - previous_time
                    if previous_status == "up":
                        uptime += duration
                    else:
                        downtime += duration
                
                previous_time = current_time
                previous_status = current_status
            
            # Handle the last observation until period_end
            if previous_status == "up":
                uptime += period_end - previous_time
            else:
                downtime += period_end - previous_time
        else:
            # If no observations, assume the last known status
            last_known_status = store_status[(store_status['store_id'] == store_id) & 
                                             (store_status['timestamp'] <= period_start)].sort_values(by='timestamp').iloc[-1]
            if last_known_status['status'] == "up":
                uptime += period_end - period_start
            else:
                downtime += period_end - period_start
    
    # Convert uptime and downtime to minutes
    return uptime.total_seconds() / 60, downtime.total_seconds() / 60

os.makedirs("reports", exist_ok=True)
