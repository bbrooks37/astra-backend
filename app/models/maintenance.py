from sqlalchemy import Column, Integer, String, Enum, Float, Date, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from app.constants import TrackingType

class MaintenanceItem(Base):
    """
    Represents a specific maintenance task for the Astra 1125SP (N528RR).
    Mapped directly from the 2026 Due List and Aircraft Status reports.
    """
    __tablename__ = "maintenance_items"

    id = Column(Integer, primary_key=True, index=True)
    task_number = Column(String, index=True)  # e.g., "27 4005"
    description = Column(String, nullable=False)
    equipment_type = Column(String, default="Airframe") # Airframe, L/H Engine, R/H Engine, APU
    
    # Tracking Configuration
    tracking_method = Column(Enum(TrackingType), default=TrackingType.WHICHEVER_FIRST)
    
    # Interval Thresholds (The "Limits")
    interval_hours = Column(Float, nullable=True)
    interval_cycles = Column(Integer, nullable=True)
    interval_months = Column(Integer, nullable=True)
    
    # Last Completion Data (The "History")
    last_completed_hours = Column(Float, nullable=True)
    last_completed_cycles = Column(Integer, nullable=True)
    last_completed_date = Column(Date, nullable=True)
    
    # Next Due Projections (The "Deadline")
    next_due_hours = Column(Float, nullable=True)
    next_due_cycles = Column(Integer, nullable=True)
    next_due_date = Column(Date, nullable=True)
    
    # Status Flags
    is_overdue = Column(Boolean, default=False)
    is_optional = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    # Relationships
    # This allows us to call item.compliance_history to see all previous sign-offs
    compliance_history = relationship("MaintenanceLog", back_populates="item", cascade="all, delete-orphan")

class MaintenanceLog(Base):
    """
    Historical record of a maintenance task completion.
    Acts as the 'Return to Service' documentation for FAA compliance.
    """
    __tablename__ = "maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("maintenance_items.id"))
    
    completion_date = Column(Date, nullable=False)
    completion_hours = Column(Float, nullable=False) # AFTT at time of maintenance
    technician_name = Column(String, nullable=False) # e.g., "R. Richards"
    work_order_ref = Column(String, nullable=True)   # e.g., "WO-9921"
    
    notes = Column(Text, nullable=True)
    
    # Relationship back to the main item
    item = relationship("MaintenanceItem", back_populates="compliance_history")

class FlightLog(Base):
    """
    Digital Flight Log for N528RR. 
    Entries here automatically drive the 'is_overdue' logic in MaintenanceItems.
    """
    __tablename__ = "flight_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    pic_name = Column(String, nullable=False)  # Pilot in Command
    sic_name = Column(String, nullable=True)   # Second in Command
    
    # Route Information
    departure_icao = Column(String(4))
    arrival_icao = Column(String(4))
    
    # Times & Cycles (Critical for Maintenance Tracking)
    flight_time = Column(Float, nullable=False) # Total hours for AFTT
    landings_day = Column(Integer, default=1)
    landings_night = Column(Integer, default=0)
    total_landings = Column(Integer) # Sum of day/night
    
    # Engine/System Data
    fuel_burn_lbs = Column(Integer)
    oil_added_lh = Column(Float, default=0.0)
    oil_added_rh = Column(Float, default=0.0)
    
    # Pilot Discrepancies (Squawks)
    squawks = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=True)