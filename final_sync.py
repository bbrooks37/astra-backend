import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import your actual models and Base from your app logic
from database import Base, engine 
from app.models.maintenance import MaintenanceItem, FlightLog, MaintenanceLog

def fix_it():
    print("🚀 Forcing database sync in the backend directory...")
    # This physically creates the tables in the .db file the API uses
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created. Now seeding initial tasks...")
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Check if empty before seeding
    if db.query(MaintenanceItem).count() == 0:
        test_task = MaintenanceItem(
            task_number="76 0015-U1",
            description="L/H Engine DEEC Download (ECTM)",
            equipment_type="L/H Engine",
            interval_hours=100.0,
            next_due_hours=4215.0,
            is_overdue=True
        )
        db.add(test_task)
        db.commit()
        print("✅ Seed task added: DEEC Download.")
    else:
        print("ℹ️ Database already contains data, skipping seed.")
    db.close()

if __name__ == "__main__":
    fix_it()