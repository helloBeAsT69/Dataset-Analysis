from typing import Dict, Any


class IntegrityScorer:
    """
    Transparent, explainable integrity scoring engine for computer vision datasets.
    Maps flaws (exact duplicates, near duplicates, and anomalous samples)
    to a 0-100 score and policy status (ACCEPT / REVIEW / QUARANTINE).
    """

    EXACT_DUP_WEIGHT = 0.50     # -0.5 points per duplicate copy
    NEAR_DUP_WEIGHT = 0.75      # -0.75 points per near-duplicate variant
    ANOMALY_WEIGHT = 1.50       # -1.5 points per anomalous / corrupted sample

    ACCEPT_THRESHOLD = 90
    REVIEW_THRESHOLD = 70

    @classmethod
    def compute(
        cls,
        duplicates: int,
        near_duplicates: int,
        anomalies: int,
        total_samples: int
    ) -> Dict[str, Any]:
        dup_penalty = round(duplicates * cls.EXACT_DUP_WEIGHT, 2)
        near_dup_penalty = round(near_duplicates * cls.NEAR_DUP_WEIGHT, 2)
        anomaly_penalty = round(anomalies * cls.ANOMALY_WEIGHT, 2)
        total_deduction = round(dup_penalty + near_dup_penalty + anomaly_penalty, 2)

        raw_score = 100.0 - total_deduction
        integrity_score = max(0, min(100, int(round(raw_score))))

        if integrity_score >= cls.ACCEPT_THRESHOLD:
            status = "ACCEPT"
            recommendation = "Dataset is clean, diversified, and meets assurance standards for CV model training."
        elif integrity_score >= cls.REVIEW_THRESHOLD:
            status = "REVIEW"
            recommendation = "Dataset exhibits moderate redundancy or minor anomalies. Manual audit / deduplication recommended before training."
        else:
            status = "QUARANTINE"
            recommendation = "High risk of data poisoning, heavy class duplication, or sensor defects. Dataset quarantined from production training pipelines."

        return {
            "integrity_score": integrity_score,
            "status": status,
            "recommendation": recommendation,
            "scoring_formula": "100 - (0.5 * duplicates + 0.75 * near_duplicates + 1.5 * anomalies)",
            "deductions": {
                "exact_duplicates": {
                    "count": duplicates,
                    "unit_weight": cls.EXACT_DUP_WEIGHT,
                    "deduction": dup_penalty
                },
                "near_duplicates": {
                    "count": near_duplicates,
                    "unit_weight": cls.NEAR_DUP_WEIGHT,
                    "deduction": near_dup_penalty
                },
                "anomalies": {
                    "count": anomalies,
                    "unit_weight": cls.ANOMALY_WEIGHT,
                    "deduction": anomaly_penalty
                },
                "total_deduction": total_deduction
            }
        }
