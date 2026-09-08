import os
import shutil
import tempfile
import zipfile
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Body, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.data_integrity.pipeline import DatasetAnalysisPipeline

router = APIRouter(tags=["Data Integrity Engine"])

pipeline = DatasetAnalysisPipeline(near_dup_threshold=6, contamination=0.08)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_COMPROMISED_DIR = os.path.join(BASE_DIR, "datasets", "compromised_demo")
DEFAULT_CLEAN_DIR = os.path.join(BASE_DIR, "datasets", "clean_demo")


class DatasetPathRequest(BaseModel):
    dataset_path: Optional[str] = Field(
        default=None,
        description="Optional local filesystem path to dataset directory. If omitted, uses demo dataset."
    )
    near_dup_threshold: Optional[int] = Field(
        default=6,
        description="Perceptual hash Hamming distance threshold (default: 6)."
    )


class DatasetAnalysisResponse(BaseModel):
    integrity_score: int
    duplicates: int
    near_duplicates: int
    anomalies: int
    status: str
    audit_details: Optional[dict] = None


@router.post(
    "/analyze-dataset",
    response_model=DatasetAnalysisResponse,
    summary="Analyze Computer Vision Dataset for Duplicates, Near-Duplicates & Anomalies"
)
async def analyze_dataset(
    file: Optional[UploadFile] = File(None, description="Optional ZIP archive containing dataset images"),
    dataset_path: Optional[str] = Query(None, description="Optional path to directory on disk")
):
    """
    Core SIH Data Integrity Engine Endpoint:
    Dataset -> Duplicate Detection -> Near Duplicate Detection -> Anomaly Detection -> Integrity Score
    """
    temp_dir = None
    try:
        # Case A: ZIP file uploaded via multipart form
        if file is not None:
            if not file.filename.lower().endswith(".zip"):
                raise HTTPException(status_code=400, detail="Only .zip dataset archives are supported for file upload.")
            
            temp_dir = tempfile.mkdtemp(prefix="sih_dataset_")
            zip_path = os.path.join(temp_dir, file.filename)
            with open(zip_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract archive
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            
            results = pipeline.run_on_directory(temp_dir)
            return results

        # Case B: Local directory path provided
        target_dir = dataset_path or DEFAULT_COMPROMISED_DIR
        
        # If relative path given, resolve relative to project root
        if not os.path.isabs(target_dir):
            target_dir = os.path.join(BASE_DIR, target_dir)

        if not os.path.exists(target_dir):
            raise HTTPException(status_code=404, detail=f"Dataset directory not found: {target_dir}")

        results = pipeline.run_on_directory(target_dir)
        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset analysis failed: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/analyze-dataset-json", response_model=DatasetAnalysisResponse)
async def analyze_dataset_json(payload: DatasetPathRequest):
    """JSON-body variant of analyze-dataset for direct API integration."""
    target_dir = payload.dataset_path or DEFAULT_COMPROMISED_DIR
    if not os.path.isabs(target_dir):
        target_dir = os.path.join(BASE_DIR, target_dir)

    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail=f"Dataset directory not found: {target_dir}")

    custom_pipeline = DatasetAnalysisPipeline(near_dup_threshold=payload.near_dup_threshold or 6)
    return custom_pipeline.run_on_directory(target_dir)


@router.get("/analyze-dataset/demo/clean", response_model=DatasetAnalysisResponse)
async def analyze_clean_demo():
    """Run analysis on the verified clean demo dataset."""
    if not os.path.exists(DEFAULT_CLEAN_DIR):
        raise HTTPException(status_code=404, detail="Clean demo dataset not found. Run dataset generator first.")
    return pipeline.run_on_directory(DEFAULT_CLEAN_DIR)


@router.get("/analyze-dataset/demo/compromised", response_model=DatasetAnalysisResponse)
async def analyze_compromised_demo():
    """Run analysis on the compromised demo dataset."""
    if not os.path.exists(DEFAULT_COMPROMISED_DIR):
        raise HTTPException(status_code=404, detail="Compromised demo dataset not found. Run dataset generator first.")
    return pipeline.run_on_directory(DEFAULT_COMPROMISED_DIR)
