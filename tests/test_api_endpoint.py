import os
import sys
import json
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.main import app

client = TestClient(app)

def test_api():
    print("1. Testing GET / (Root Info)...")
    res = client.get("/")
    assert res.status_code == 200, f"Root returned {res.status_code}"
    print("   Root OK:", res.json()["platform"])

    print("\n2. Testing POST /analyze-dataset (Default Compromised Dataset)...")
    res = client.post("/analyze-dataset")
    assert res.status_code == 200, f"POST /analyze-dataset failed: {res.text}"
    data = res.json()
    print("   Output JSON:")
    print(json.dumps({
        "integrity_score": data["integrity_score"],
        "duplicates": data["duplicates"],
        "near_duplicates": data["near_duplicates"],
        "anomalies": data["anomalies"],
        "status": data["status"]
    }, indent=2))

    # Assert exact user requirements
    assert data["integrity_score"] == 82, f"Expected 82, got {data['integrity_score']}"
    assert data["duplicates"] == 12, f"Expected 12, got {data['duplicates']}"
    assert data["near_duplicates"] == 8, f"Expected 8, got {data['near_duplicates']}"
    assert data["anomalies"] == 4, f"Expected 4, got {data['anomalies']}"
    assert data["status"] == "REVIEW", f"Expected REVIEW, got {data['status']}"
    print("   All assertions passed for compromised dataset!")

    print("\n3. Testing GET /analyze-dataset/demo/clean (Clean Baseline)...")
    res_clean = client.get("/analyze-dataset/demo/clean")
    assert res_clean.status_code == 200
    clean_data = res_clean.json()
    print("   Clean Output JSON:")
    print(json.dumps({
        "integrity_score": clean_data["integrity_score"],
        "duplicates": clean_data["duplicates"],
        "near_duplicates": clean_data["near_duplicates"],
        "anomalies": clean_data["anomalies"],
        "status": clean_data["status"]
    }, indent=2))
    assert clean_data["integrity_score"] == 100
    assert clean_data["status"] == "ACCEPT"
    print("   Clean baseline verified!")

if __name__ == "__main__":
    test_api()
