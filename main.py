import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, timedelta
from pydantic import BaseModel

from database import get_db
from app.models.maintenance import MaintenanceItem, FlightLog, MaintenanceLog

app = FastAPI(title="Astra 1125SP Fleet Manager")

# UPDATED CORS: Added your Vercel production URL
origins = [
    "http://localhost:5173",                          # Local Vite Dev
    "http://127.0.0.1:5173",                        # Local Vite Dev Alternate
    "https://astra-frontend-tau.vercel.app",
    "https://astra-frontend-tau.vercel.app/"         
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC SCHEMAS ---
class FlightLogCreate(BaseModel):
    date: date
    pic_name: str
    departure_icao: str
    arrival_icao: str
    flight_time: float
    landings_day: int = 1
    landings_night: int = 0
    fuel_burn_lbs: Optional[int] = None
    squawks: Optional[str] = None

class MaintCompletionCreate(BaseModel):
    item_id: int
    completion_date: date
    completion_hours: float
    technician_name: str
    work_order_ref: Optional[str] = None
    notes: Optional[str] = None

# --- HELPER FUNCTIONS ---
def get_current_totals(db: Session):
    total_hours = db.query(func.sum(FlightLog.flight_time)).scalar() or 0.0
    total_landings = db.query(func.sum(FlightLog.landings_day + FlightLog.landings_night)).scalar() or 0
    # Baseline for N528RR
    return 4213.4 + total_hours, 3002 + total_landings

# --- ROUTES ---

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    try:
        aftt, cycles = get_current_totals(db)
        return {
            "aircraft": "N528RR",
            "status": "Operational",
            "current_aftt": round(aftt, 1),
            "total_cycles": cycles,
            "total_flights_logged": db.query(FlightLog).count(),
            "message": "Hangar Online"
        }
    except Exception as e:
        print(f"CRITICAL BACKEND ERROR: {e}")
        return {
            "aircraft": "N528RR",
            "status": "Maintenance Mode",
            "current_aftt": 4213.4,
            "total_cycles": 3002,
            "error": str(e)
        }

@app.get("/maintenance")
def get_all_maintenance(db: Session = Depends(get_db)):
    return db.query(MaintenanceItem).all()

@app.get("/maintenance/{item_id}/history")
def get_maintenance_history(item_id: int, db: Session = Depends(get_db)):
    return db.query(MaintenanceLog)\
             .filter(MaintenanceLog.item_id == item_id)\
             .order_by(MaintenanceLog.completion_date.desc())\
             .all()

@app.get("/logs/flights")
def get_flight_logs(db: Session = Depends(get_db)):
    return db.query(FlightLog).order_by(FlightLog.date.desc()).all()

@app.post("/logs/submit")
def submit_flight_log(log_data: FlightLogCreate, db: Session = Depends(get_db)):
    try:
        new_log = FlightLog(**log_data.model_dump(), total_landings=log_data.landings_day + log_data.landings_night)
        db.add(new_log)
        db.flush()

        aftt, cycles = get_current_totals(db)
        items = db.query(MaintenanceItem).all()
        for item in items:
            if (item.next_due_hours and aftt >= item.next_due_hours) or \
               (item.next_due_cycles and cycles >= item.next_due_cycles) or \
               (item.next_due_date and date.today() >= item.next_due_date):
                item.is_overdue = True

        db.commit()
        return {"status": "Log Processed", "new_aftt": round(aftt, 1)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/maintenance/complete")
def complete_maintenance_task(data: MaintCompletionCreate, db: Session = Depends(get_db)):
    item = db.query(MaintenanceItem).filter(MaintenanceItem.id == data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Maintenance task not found")

    try:
        new_history = MaintenanceLog(
            item_id=data.item_id,
            completion_date=data.completion_date,
            completion_hours=data.completion_hours,
            technician_name=data.technician_name,
            work_order_ref=data.work_order_ref,
            notes=data.notes
        )
        db.add(new_history)

        item.last_completed_date = data.completion_date
        item.last_completed_hours = data.completion_hours
        
        if item.interval_hours:
            item.next_due_hours = data.completion_hours + item.interval_hours
        
        if item.interval_months:
            item.next_due_date = data.completion_date + timedelta(days=item.interval_months * 30)

        item.is_overdue = False
        
        db.commit()
        return {"status": "Task Signed Off", "task": item.description, "next_due": item.next_due_hours}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Added for deployment: Ensures the app listens on the port assigned by the host
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)