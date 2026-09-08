import os
import sys
import json

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.modules.data_integrity.pipeline import DatasetAnalysisPipeline

def run_verification():
    clean_dir = os.path.join(BASE_DIR, "datasets", "clean_demo")
    compromised_dir = os.path.join(BASE_DIR, "datasets", "compromised_demo")

    pipeline = DatasetAnalysisPipeline(near_dup_threshold=6, contamination=0.08)

    print("=== TESTING CLEAN DATASET ===")
    clean_results = pipeline.run_on_directory(clean_dir)
    print(json.dumps({
        "integrity_score": clean_results["integrity_score"],
        "duplicates": clean_results["duplicates"],
        "near_duplicates": clean_results["near_duplicates"],
        "anomalies": clean_results["anomalies"],
        "status": clean_results["status"]
    }, indent=2))

    print("\n=== TESTING COMPROMISED DATASET ===")
    comp_results = pipeline.run_on_directory(compromised_dir)
    print(json.dumps({
        "integrity_score": comp_results["integrity_score"],
        "duplicates": comp_results["duplicates"],
        "near_duplicates": comp_results["near_duplicates"],
        "anomalies": comp_results["anomalies"],
        "status": comp_results["status"]
    }, indent=2))

    print("\nAudit Details for Compromised Dataset:")
    print(f"- Exact duplicate groups: {len(comp_results['audit_details']['exact_duplicate_groups'])}")
    print(f"- Near duplicate pairs: {len(comp_results['audit_details']['near_duplicate_pairs'])}")
    print(f"- Flagged anomalies: {len(comp_results['audit_details']['anomalies'])}")
    for a in comp_results['audit_details']['anomalies']:
        print(f"  * {a['filename']}: {a['reason']}")

    return clean_results, comp_results

if __name__ == "__main__":
    run_verification()
