from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Text, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class RoleEnum(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.PATIENT, nullable=False)
    
    reports = relationship("Report", back_populates="patient", foreign_keys="Report.patient_id")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="uploaded") # uploaded, processed, verified
    ai_summary = Column(Text, nullable=True)     # <--- ADDED THIS FIELD
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("User", back_populates="reports", foreign_keys=[patient_id])
    extractions = relationship("ExtractedValue", back_populates="report", cascade="all, delete-orphan")
    clinical_note = relationship("ClinicalNote", back_populates="report", uselist=False, cascade="all, delete-orphan")

class ExtractedValue(Base):
    __tablename__ = "extracted_values"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    test_name = Column(String, nullable=False)
    result_value = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    reference_range = Column(String, nullable=True)
    is_out_of_range = Column(Boolean, default=False)
    evidence_snippet = Column(Text, nullable=True) # Source snippet from OCR
    is_verified = Column(Boolean, default=False)
    corrected_value = Column(String, nullable=True)
    
    report = relationship("Report", back_populates="extractions")

class ClinicalNote(Base):
    __tablename__ = "clinical_notes"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="clinical_note")