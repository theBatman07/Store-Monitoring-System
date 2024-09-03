# Store Monitoring System

## Overview

This project provides a backend system for monitoring the uptime and downtime of restaurants based on their business hours. The system ingests data from three sources (store activity logs, business hours, and timezone information) and provides API endpoints to generate and retrieve reports on store uptime and downtime.

## Features

- **Data Ingestion**: The system reads and stores data from CSV files into a database. This includes store activity logs, business hours, and timezone information.
- **Report Generation**: A report is generated that calculates the uptime and downtime of each store within the last hour, day, and week based on the ingested data.
- **API Endpoints**:
  - `/trigger_report`: Initiates the report generation process.
  - `/get_report`: Retrieves the status of the report and, if complete, returns the report as a CSV file.

## Report Schema

The generated report contains the following columns:

- `store_id`: Unique identifier for the store.
- `uptime_last_hour (in minutes)`
- `uptime_last_day (in hours)`
- `uptime_last_week (in hours)`
- `downtime_last_hour (in minutes)`
- `downtime_last_day (in hours)`
- `downtime_last_week (in hours)`

## API Endpoints

### 1. `/trigger_report`

- **Method**: `POST`
- **Description**: Initiates the report generation process.
- **Response**:
  - `report_id`: A unique identifier for the report.

### 2. `/get_report`

- **Method**: `GET`
- **Description**: Retrieves the status of the report generation process.
- **Input**:
  - `report_id`: The unique identifier for the report.
- **Response**:
  - If the report is still being generated, returns `"Running"`.
  - If the report is complete, returns `"Complete"` and provides the report as a downloadable CSV file.

# Setup and Installation

- Clone the repo
  
  ```bash
  git clone 
  ```
  
- Install requirenments.txt
  

```bash
pip install -r requirenments.txt
```

- Make a postgres database name loop_ai
  
- Put the database url in .env
  
  ```
  DATABASE_URL=""
  ```
  
- Run the app
  

```bash
uvicorn app.main:app --reload --port 8080
```

# Tech Stack

- Python
  
- Postgres
  
- Fastapi
  
- Pandas