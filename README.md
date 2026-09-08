# AI Assurance Guardian - Dataset Analysis Engine

> **Smart India Hackathon (PS ID 26228) — Theme: Blockchain & Cybersecurity**  
> An offline AI security platform for verifying trustworthiness in multi-contributor computer vision pipelines.

---

## 🎯 Architecture Overview

```
Dataset (Directory or Uploaded ZIP)
   │
   ├──> 1. Exact Duplicate Detection (Cryptographic SHA-256 Hashing)
   │
   ├──> 2. Near Duplicate Detection (Perceptual Hashing: dHash / pHash)
   │
   ├──> 3. Anomaly Detection (Statistical CV Heuristics + Isolation Forest)
   │
   └──> 4. Explainable Integrity Scorer (ACCEPT / REVIEW / QUARANTINE)
```

---

## 🚀 Key Features

- **Exact Duplicate Detection**: Uses SHA-256 block hashing to detect identical byte-level clones with zero collision probability.
- **Perceptual Near-Duplicate Detection**: Evaluates difference hash (dHash) and discrete cosine transform perceptual hash (pHash) with Hamming distance thresholds to detect resized, re-compressed, cropped, or slightly altered image duplicates.
- **Computer Vision Anomaly Detection**: Combines low-level signal integrity checks (blackouts, whiteout glare, high-entropy sensor static, channel dropouts) with scikit-learn `IsolationForest` on multidimensional color/texture feature representations.
- **Explainable Scoring Engine**: Transparent mathematical penalty formula with deterministic policy thresholds (`ACCEPT`, `REVIEW`, `QUARANTINE`).
- **Air-Gapped & Offline Ready**: Runs 100% locally with zero external network or cloud dependencies.

---

## 📊 End-of-Day Deliverable: `POST /analyze-dataset`

### Expected Output Format
```json
{
  "integrity_score": 82,
  "duplicates": 12,
  "near_duplicates": 8,
  "anomalies": 4,
  "status": "REVIEW"
}
```

### Clean Baseline Comparison
```json
{
  "integrity_score": 100,
  "duplicates": 0,
  "near_duplicates": 0,
  "anomalies": 0,
  "status": "ACCEPT"
}
```

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── routers/
│   │   │   └── data_integrity.py    # POST /analyze-dataset & demo routes
│   │   └── modules/
│   │       └── data_integrity/
│   │           ├── duplicate_detector.py  # SHA-256 & dHash/pHash
│   │           ├── anomaly_detector.py    # Isolation Forest & CV checks
│   │           ├── scorer.py              # Transparent score calculator
│   │           └── pipeline.py            # End-to-end coordinator
│   └── requirements.txt             # Python dependencies
├── datasets/
│   ├── clean_demo/                  # 50 verified clean CV samples
│   ├── compromised_demo/            # 50 samples (12 exact dup, 8 near dup, 4 anom)
│   ├── clean_demo.zip               # Portable clean dataset archive
│   └── compromised_demo.zip         # Portable compromised dataset archive
├── scripts/
│   └── generate_demo_datasets.py    # Synthetic CV dataset generator
├── tests/
│   ├── test_dataset_analysis.py     # Pipeline unit verification
│   └── test_api_endpoint.py         # HTTP endpoint test suite
└── README.md
```

---

## 🛠️ Quick Start

### 1. Setup Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r backend/requirements.txt
```

### 2. Generate Demo Datasets
```bash
python scripts/generate_demo_datasets.py
```

### 3. Run Automated Tests
```bash
python tests/test_dataset_analysis.py
python tests/test_api_endpoint.py
```

### 4. Start the FastAPI Server
```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).
