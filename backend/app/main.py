import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure app directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routers.data_integrity import router as data_integrity_router

app = FastAPI(
    title="AI Assurance Guardian API",
    version="1.0.0",
    description="Offline AI Security Platform for Verifying Trustworthiness in Multi-Contributor Computer Vision Pipelines (SIH PS ID 26228)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local dashboards and decoupled frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(data_integrity_router)
app.include_router(data_integrity_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "platform": "AI Assurance Guardian",
        "theme": "Blockchain & Cybersecurity (SIH PS ID 26228)",
        "status": "OPERATIONAL",
        "mode": "AIR_GAPPED_OFFLINE",
        "active_modules": [
            "Data Integrity & Deduplication Engine",
            "Perceptual Near-Duplicate Analyzer",
            "Image Anomaly & Noise Isolation Engine",
            "Explainable Risk Scorer"
        ],
        "endpoints": {
            "analyze_dataset": "POST /analyze-dataset",
            "clean_demo": "GET /analyze-dataset/demo/clean",
            "compromised_demo": "GET /analyze-dataset/demo/compromised",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-assurance-guardian-backend",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
