import os
import math
import numpy as np
from typing import Dict, List, Any
from PIL import Image
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """
    Combines deterministic CV physical checks with an unsupervised Isolation Forest
    to detect corrupted, noisy, out-of-distribution, or sensor-blinded images.
    """

    def __init__(self, outlier_threshold: float = -0.09, contamination: float = 0.08, random_state: int = 42):
        self.outlier_threshold = outlier_threshold
        self.contamination = contamination
        self.random_state = random_state

    @staticmethod
    def calculate_entropy(img_gray: np.ndarray) -> float:
        """Compute Shannon entropy of the image intensity histogram."""
        hist, _ = np.histogram(img_gray, bins=256, range=(0, 256), density=True)
        hist = hist[hist > 0]
        return float(-np.sum(hist * np.log2(hist)))

    @staticmethod
    def calculate_laplacian_variance(img_gray: np.ndarray) -> float:
        """Approximate Laplacian variance (edge frequency / focus measure)."""
        padded = np.pad(img_gray.astype(np.float32), 1, mode='edge')
        laplacian = (
            -4 * padded[1:-1, 1:-1]
            + padded[:-2, 1:-1]
            + padded[2:, 1:-1]
            + padded[1:-1, :-2]
            + padded[1:-1, 2:]
        )
        return float(np.var(laplacian))

    def extract_features(self, img_rgb: Image.Image) -> Dict[str, Any]:
        """Extract multi-dimensional computer vision feature vectors and heuristics."""
        arr = np.array(img_rgb)
        gray = np.array(img_rgb.convert("L"))

        r = arr[:, :, 0].astype(np.float32)
        g = arr[:, :, 1].astype(np.float32)
        b = arr[:, :, 2].astype(np.float32)

        mean_r, std_r = float(np.mean(r)), float(np.std(r))
        mean_g, std_g = float(np.mean(g)), float(np.std(g))
        mean_b, std_b = float(np.mean(b)), float(np.std(b))

        gray_mean, gray_std = float(np.mean(gray)), float(np.std(gray))
        entropy = self.calculate_entropy(gray)
        laplacian_var = self.calculate_laplacian_variance(gray)

        # Domain Heuristics for Computer Vision Pipelines
        heuristic_anomaly = None
        if gray_mean < 8.0 and gray_std < 6.0:
            heuristic_anomaly = f"Camera Lens Occlusion / Sensor Blackout (Mean={gray_mean:.1f})"
        elif gray_mean > 248.0 and gray_std < 10.0:
            heuristic_anomaly = f"Glare / Sensor Saturation Whiteout (Mean={gray_mean:.1f})"
        elif entropy > 7.7 and laplacian_var > 3500.0:
            heuristic_anomaly = f"Extreme Sensor Noise / High Entropy Static (Entropy={entropy:.2f})"
        elif mean_g < 5.0 and mean_r > 150.0 and mean_b > 150.0:
            heuristic_anomaly = f"Hardware Channel Dropout / Signal Inversion Fault (Mean G={mean_g:.1f})"

        vector = [
            mean_r, std_r,
            mean_g, std_g,
            mean_b, std_b,
            gray_mean, gray_std,
            entropy,
            math.log(max(1.0, laplacian_var))
        ]

        return {
            "vector": vector,
            "heuristic_anomaly": heuristic_anomaly,
            "metrics": {
                "gray_mean": round(gray_mean, 2),
                "gray_std": round(gray_std, 2),
                "entropy": round(entropy, 2),
                "laplacian_var": round(laplacian_var, 2)
            }
        }

    def detect(self, file_paths: List[str]) -> Dict[str, Any]:
        if not file_paths:
            return {"anomalies_count": 0, "anomalies": []}

        features_list = []
        corrupted = []

        for path in file_paths:
            try:
                with Image.open(path) as img:
                    img_rgb = img.convert("RGB")
                    feat = self.extract_features(img_rgb)
                    feat["filename"] = os.path.basename(path)
                    feat["path"] = path
                    features_list.append(feat)
            except Exception as e:
                corrupted.append({
                    "filename": os.path.basename(path),
                    "reason": f"Corrupted image payload: {str(e)}",
                    "severity": "CRITICAL"
                })

        if not features_list:
            return {"anomalies_count": len(corrupted), "anomalies": corrupted}

        # Train Isolation Forest on dataset feature representations
        vectors = np.array([f["vector"] for f in features_list])
        iso_forest = IsolationForest(
            random_state=self.random_state,
            n_estimators=100
        )
        iso_forest.fit(vectors)
        scores = iso_forest.decision_function(vectors)

        anomalies = list(corrupted)
        for i, feat in enumerate(features_list):
            is_anomaly = False
            reasons = []

            # 1. Deterministic heuristic triggered
            if feat["heuristic_anomaly"]:
                is_anomaly = True
                reasons.append(feat["heuristic_anomaly"])

            # 2. Strong Isolation Forest Outlier
            if scores[i] < self.outlier_threshold:
                is_anomaly = True
                reasons.append(f"Statistical Feature Outlier (Isolation Forest Score: {scores[i]:.3f})")

            if is_anomaly:
                anomalies.append({
                    "filename": feat["filename"],
                    "path": feat["path"],
                    "reason": "; ".join(reasons),
                    "metrics": feat["metrics"],
                    "ml_anomaly_score": round(float(scores[i]), 4)
                })

        return {
            "anomalies_count": len(anomalies),
            "anomalies": anomalies
        }
