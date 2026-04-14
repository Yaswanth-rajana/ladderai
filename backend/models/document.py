from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None

class ExtractedData(BaseModel):
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    line_items: List[LineItem] = []

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    created_at: datetime
    extracted_data: Optional[ExtractedData] = None
    validation_errors: List[str] = []
    confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None
    pages: Optional[int] = None
    
    class Config:
        from_attributes = True