from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="LadderAI Document Intelligence",
    description="Invoice extraction and validation system",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes import documents
app.include_router(documents.router)

# Health check endpoint
@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "LadderAI Document Intelligence",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# Import and include routes (will add after Phase 2)
# from routes import documents
# app.include_router(documents.router)