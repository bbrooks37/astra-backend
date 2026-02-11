from datetime import date
from database import SessionLocal, engine, Base
from app.models.maintenance import MaintenanceItem, FlightLog
from app.constants import TrackingType
import sqlalchemy as sa

def seed_data():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)
    inspector = sa.inspect(engine)
    
    try:
        # 1. SAFELY CLEAN OLD DATA
        # We check if tables exist first to avoid the "UndefinedTable" error
        if inspector.has_table("maintenance_items"):
            db.query(MaintenanceItem).delete()
        if inspector.has_table("flight_logs"):
            db.query(FlightLog).delete()
        db.commit()

        # 2. DEFINE THE ASTRA N528RR DATASET
        items = [
            # Airframe Overdue Item
            MaintenanceItem(
                task_number="27 4005",
                description="Horizontal Stabilizer Trim Actuator Seal - Lubrication",
                equipment_type="Airframe",
                tracking_method=TrackingType.CALENDAR,
                interval_months=24,
                last_completed_hours=4092.0,
                last_completed_date=date(2024, 2, 2),
                next_due_date=date(2026, 2, 2), 
                is_overdue=True,
                notes="Past Due per 2026 Due List - Action Required"
            ),
            # Engine Cycle Item
            MaintenanceItem(
                task_number="76 0015-U1",
                description="L/H Engine DEEC Download (ECTM)",
                equipment_type="L/H Engine",
                tracking_method=TrackingType.CYCLES,
                interval_cycles=40,
                last_completed_hours=4146.3,
                last_completed_cycles=2940,
                last_completed_date=date(2024, 7, 24),
                next_due_cycles=2980,
                is_overdue=False
            ),
            # Safety Item
            MaintenanceItem(
                task_number="26 2406.1",
                description="Cockpit Portable Halon Fire Extinguisher HEFT Check",
                equipment_type="Airframe",
                tracking_method=TrackingType.CALENDAR,
                interval_months=1,
                last_completed_hours=4213.4,
                last_completed_date=date(2026, 1, 19),
                next_due_date=date(2026, 2, 18),
                is_overdue=False
            ),
            # Hourly Engine Inspection
            MaintenanceItem(
                task_number="72 3101",
                description="No. 1 Engine Fan Rotor Blade FOD Inspection",
                equipment_type="L/H Engine",
                tracking_method=TrackingType.HOURS,
                interval_hours=300.0,
                last_completed_hours=3939.4,
                next_due_hours=4239.4,
                is_overdue=False,
                notes="Next due in ~26 flight hours."
            )
        ]

        db.add_all(items)
        db.commit()
        print(f"✅ SUCCESS: Seeded {len(items)} maintenance tasks for N528RR.")
        print("🚀 Current AFTT Baseline: 4213.4 | Total Landings: 3002")

    except Exception as e:
        db.rollback()
        print(f"❌ SEED ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()