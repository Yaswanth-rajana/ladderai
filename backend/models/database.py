from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./invoices.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class InvoiceModel(Base):
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.now)
    
    # Extracted data as JSON
    extracted_data = Column(JSON, nullable=True)
    validation_errors = Column(JSON, default=[])
    confidence = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    pages = Column(Integer, nullable=True)
    
    # Metadata
    prompt_version_used = Column(String, default="v1")
    error = Column(String, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()