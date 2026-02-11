import sys
import os

# This line tells Python to look in the current folder for the 'app' package
sys.path.append(os.getcwd())

from database import engine, Base
from app.models.maintenance import MaintenanceItem

def init_hangar():
    print("Connecting to PostgreSQL 18...")
    Base.metadata.create_all(bind=engine)
    print("SUCCESS: 'maintenance_items' table created.")

if __name__ == "__main__":
    init_hangar()