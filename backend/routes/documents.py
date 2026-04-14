from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from services.parser import PDFParser
from services.extractor import InvoiceExtractor
from services.normalizer import DataNormalizer
from services.validator import InvoiceValidator
from models.database import get_db, InvoiceModel
from models.document import DocumentResponse, ExtractedData

router = APIRouter(prefix="/documents", tags=["documents"])

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize services
parser = PDFParser()
extractor = InvoiceExtractor()
normalizer = DataNormalizer()
validator = InvoiceValidator()

def process_document(document_id: str, db: Session):
    """
    Background task to process PDF
    """
    import time
    start_time = time.time()
    
    # Get document from database
    document = db.query(InvoiceModel).filter(InvoiceModel.id == document_id).first()
    if not document:
        return
    
    # Update status
    document.status = "processing"
    db.commit()
    
    # Parse PDF
    pdf_path = document.file_path
    result = parser.parse(pdf_path)
    
    if result["success"]:
        # Extract structured data
        extracted_data = extractor.extract(result["text"])
        
        # Normalize
        normalized_data = normalizer.normalize(extracted_data)
        
        # Validate
        validation_errors, confidence = validator.validate(normalized_data)
        
        # Update document
        document.extracted_data = normalized_data
        document.validation_errors = validation_errors
        document.confidence = confidence
        document.pages = result["pages"]
        document.status = "completed"
        document.processing_time_ms = (time.time() - start_time) * 1000
        
        print(f"✅ Processed {document_id} in {document.processing_time_ms:.0f}ms")
        print(f"   Confidence: {confidence}%")
    else:
        document.status = "failed"
        document.error = result["error"]
        print(f"❌ Failed to parse {document_id}: {result['error']}")
    
    db.commit()

@router.post("/upload")
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a single invoice PDF
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Generate unique ID
    document_id = str(uuid.uuid4())
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{document_id}.pdf")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create database record
    document = InvoiceModel(
        id=document_id,
        filename=file.filename,
        file_path=file_path,
        status="pending",
        created_at=datetime.now()
    )
    
    db.add(document)
    db.commit()
    
    # Process in background
    background_tasks.add_task(process_document, document_id, db)
    
    return JSONResponse(
        status_code=202,
        content={
            "message": "Invoice uploaded successfully",
            "document_id": document_id,
            "status": "pending"
        }
    )

@router.post("/upload/bulk")
async def upload_bulk_invoices(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple invoice PDFs at once
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per bulk upload")
    
    results = []
    for file in files:
        if not file.filename.endswith('.pdf'):
            continue
        
        document_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}.pdf")
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            # Skip failed files or handle error
            continue
        
        document = InvoiceModel(
            id=document_id,
            filename=file.filename,
            file_path=file_path,
            status="pending",
            created_at=datetime.now()
        )
        
        db.add(document)
        db.commit()
        
        background_tasks.add_task(process_document, document_id, db)
        
        results.append({
            "document_id": document_id,
            "filename": file.filename,
            "status": "pending"
        })
    
    return {
        "message": f"Successfully uploaded {len(results)} invoices",
        "documents": results
    }

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    """
    List all processed invoices
    """
    documents = db.query(InvoiceModel).order_by(InvoiceModel.created_at.desc()).all()
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """
    Get extracted data for a specific invoice
    """
    document = db.query(InvoiceModel).filter(InvoiceModel.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

@router.post("/reprocess/{document_id}")
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Reprocess an existing document
    """
    document = db.query(InvoiceModel).filter(InvoiceModel.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Reset status
    document.status = "pending"
    document.extracted_data = None
    document.validation_errors = []
    document.confidence = None
    document.processing_time_ms = None
    db.commit()
    
    # Reprocess
    background_tasks.add_task(process_document, document_id, db)
    
    return {
        "message": "Reprocessing started",
        "document_id": document_id
    }

@router.get("/stats/summary")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get processing statistics
    """
    documents = db.query(InvoiceModel).all()
    
    total = len(documents)
    completed = len([d for d in documents if d.status == "completed"])
    failed = len([d for d in documents if d.status == "failed"])
    
    avg_confidence = 0
    avg_processing_time = 0
    
    completed_docs = [d for d in documents if d.confidence is not None]
    if completed_docs:
        avg_confidence = sum(d.confidence for d in completed_docs) / len(completed_docs)
        avg_processing_time = sum(d.processing_time_ms for d in completed_docs if d.processing_time_ms) / len(completed_docs)
    
    return {
        "total_documents": total,
        "completed": completed,
        "failed": failed,
        "success_rate": (completed / total * 100) if total > 0 else 0,
        "average_confidence": round(avg_confidence, 1),
        "average_processing_time_ms": round(avg_processing_time, 2)
    }