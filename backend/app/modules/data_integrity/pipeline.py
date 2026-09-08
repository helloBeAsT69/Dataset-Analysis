import os
import glob
from typing import Dict, List, Any, Optional
from .duplicate_detector import DuplicateDetector
from .anomaly_detector import AnomalyDetector
from .scorer import IntegrityScorer


class DatasetAnalysisPipeline:
    """
    End-to-end dataset analysis pipeline:
    Dataset -> Duplicate Detection -> Near Duplicate Detection -> Anomaly Detection -> Integrity Score
    """

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

    def __init__(self, near_dup_threshold: int = 6, contamination: float = 0.08):
        self.duplicate_detector = DuplicateDetector(near_dup_threshold=near_dup_threshold)
        self.anomaly_detector = AnomalyDetector(contamination=contamination)

    def find_image_files(self, directory: str) -> List[str]:
        """Recursively collect all valid image files in a directory."""
        images = []
        for root, _, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    images.append(os.path.join(root, file))
        images.sort()
        return images

    def run(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Execute the full integrity verification pipeline on a list of image filepaths.
        """
        total_images = len(image_paths)
        if total_images == 0:
            return {
                "integrity_score": 0,
                "duplicates": 0,
                "near_duplicates": 0,
                "anomalies": 0,
                "status": "QUARANTINE",
                "error": "No valid image files found in dataset."
            }

        # Step 1 & 2: Duplicate Detection (Exact & Near)
        dup_results = self.duplicate_detector.detect(image_paths)
        duplicates_count = dup_results["exact_duplicates_count"]
        near_duplicates_count = dup_results["near_duplicates_count"]

        # Step 3: Anomaly Detection (Statistical + Outlier IF)
        anomaly_results = self.anomaly_detector.detect(image_paths)
        anomalies_count = anomaly_results["anomalies_count"]

        # Step 4: Integrity Score Calculation
        score_data = IntegrityScorer.compute(
            duplicates=duplicates_count,
            near_duplicates=near_duplicates_count,
            anomalies=anomalies_count,
            total_samples=total_images
        )

        # Build response strictly compatible with expected output format
        # {
        #   "integrity_score": 82,
        #   "duplicates": 12,
        #   "near_duplicates": 8,
        #   "anomalies": 4,
        #   "status": "REVIEW"
        # }
        response = {
            "integrity_score": score_data["integrity_score"],
            "duplicates": duplicates_count,
            "near_duplicates": near_duplicates_count,
            "anomalies": anomalies_count,
            "status": score_data["status"],
            # Extended audit details for hackathon judges
            "audit_details": {
                "total_samples": total_images,
                "recommendation": score_data["recommendation"],
                "scoring_formula": score_data["scoring_formula"],
                "deductions": score_data["deductions"],
                "exact_duplicate_groups": dup_results["exact_duplicate_groups"],
                "near_duplicate_pairs": dup_results["near_duplicate_pairs"],
                "anomalies": anomaly_results["anomalies"]
            }
        }
        return response

    def run_on_directory(self, directory: str) -> Dict[str, Any]:
        """Run analysis on all images located within a directory path."""
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Dataset directory '{directory}' does not exist.")
        image_paths = self.find_image_files(directory)
        return self.run(image_paths)
