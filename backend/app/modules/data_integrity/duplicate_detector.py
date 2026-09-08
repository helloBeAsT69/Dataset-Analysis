import hashlib
import os
from typing import Dict, List, Any
from PIL import Image
import imagehash


class DuplicateDetector:
    """
    Detects exact duplicate images (SHA-256 cryptographic hash collision)
    and perceptual near-duplicates (perceptual hashing with configurable Hamming distance threshold).
    """

    def __init__(self, near_dup_threshold: int = 5):
        """
        :param near_dup_threshold: Maximum dHash Hamming distance for near duplicate matching.
        """
        self.near_dup_threshold = near_dup_threshold

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        """Compute SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def compute_perceptual_hashes(image: Image.Image) -> Dict[str, Any]:
        """Compute perceptual hashes (dHash and pHash)."""
        gray = image.convert("L")
        return {
            "dhash": imagehash.dhash(gray),
            "phash": imagehash.phash(gray)
        }

    def detect(self, file_paths: List[str]) -> Dict[str, Any]:
        exact_hash_map: Dict[str, List[str]] = {}
        file_records = []
        corrupted_files = []

        # 1. Exact Duplicate Detection via SHA-256
        for path in file_paths:
            fname = os.path.basename(path)
            try:
                sha = self.compute_sha256(path)
                exact_hash_map.setdefault(sha, []).append(path)

                with Image.open(path) as img:
                    img_rgb = img.convert("RGB")
                    hashes = self.compute_perceptual_hashes(img_rgb)
                    file_records.append({
                        "path": path,
                        "filename": fname,
                        "sha256": sha,
                        "dhash": hashes["dhash"],
                        "phash": hashes["phash"]
                    })
            except Exception as e:
                corrupted_files.append({"filename": fname, "path": path, "error": str(e)})

        # Group exact duplicates
        exact_duplicate_groups = []
        exact_duplicate_count = 0
        exact_redundant_files = set()

        for sha, paths in exact_hash_map.items():
            if len(paths) > 1:
                # Prefer original sample files over duplicate clones as canonical
                paths.sort(key=lambda p: (1 if any(k in os.path.basename(p).lower() for k in ["dup", "copy", "clone"]) else 0, p))
                canonical = paths[0]
                duplicates = paths[1:]
                exact_duplicate_count += len(duplicates)
                for dup in duplicates:
                    exact_redundant_files.add(dup)
                exact_duplicate_groups.append({
                    "sha256": sha,
                    "canonical_file": os.path.basename(canonical),
                    "duplicate_files": [os.path.basename(p) for p in duplicates],
                    "count": len(duplicates)
                })

        # 2. Near Duplicate Detection (excluding exact duplicates to prevent double-counting)
        canonical_records = [r for r in file_records if r["path"] not in exact_redundant_files]
        near_duplicate_pairs = []
        near_duplicate_files = set()

        n = len(canonical_records)
        for i in range(n):
            for j in range(i + 1, n):
                rec_a = canonical_records[i]
                rec_b = canonical_records[j]

                dist_d = int(rec_a["dhash"] - rec_b["dhash"])
                dist_p = int(rec_a["phash"] - rec_b["phash"])

                # Criteria: dHash <= threshold AND pHash <= 10
                if dist_d <= self.near_dup_threshold and dist_p <= 10:
                    similarity_pct = round((1.0 - (dist_d / 64.0)) * 100, 2)
                    near_duplicate_pairs.append({
                        "file_a": rec_a["filename"],
                        "file_b": rec_b["filename"],
                        "hamming_distance": dist_d,
                        "similarity_percentage": similarity_pct,
                        "algorithm": "dhash+phash"
                    })
                    near_duplicate_files.add(rec_b["filename"])

        return {
            "exact_duplicates_count": exact_duplicate_count,
            "exact_duplicate_groups": exact_duplicate_groups,
            "near_duplicates_count": len(near_duplicate_files),
            "near_duplicate_pairs": near_duplicate_pairs,
            "corrupted_files": corrupted_files
        }
