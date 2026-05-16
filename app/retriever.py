"""
retriever.py — Loads FAISS index and retrieves relevant assessments.

This is the ONLY place that touches the vector index.
The rest of the app calls search() and gets back a clean list of dicts.

Why keep this separate?
- Easy to test independently
- Easy to swap FAISS for another DB later
- Single responsibility: retriever retrieves, nothing else
"""

import json
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "data", "faiss_index", "index.faiss")
META_PATH  = os.path.join(BASE_DIR, "data", "faiss_index", "metadata.json")

MODEL_NAME = "all-MiniLM-L6-v2"

# ── Load once at startup ───────────────────────────────────────────────────
# We load these into module-level variables so they are loaded ONCE
# when the server starts, not on every request. This keeps responses fast.
print("Loading FAISS index and embedding model...")
_index    = faiss.read_index(INDEX_PATH)
_model    = SentenceTransformer(MODEL_NAME)
with open(META_PATH, encoding="utf-8") as f:
    _metadata = json.load(f)
print(f"Retriever ready — {_index.ntotal} assessments indexed.")


def search(query: str, top_k: int = 10) -> list[dict]:
    """
    Convert query to a vector and find the top_k most similar assessments.

    Args:
        query:  Natural language search string (e.g. "Java developer test")
        top_k:  How many results to return (max 10 per assignment rules)

    Returns:
        List of assessment dicts from metadata.json, ordered by relevance.
    """
    # Convert the query string into a vector
    query_vec = _model.encode([query], convert_to_numpy=True)

    # Normalize so dot product = cosine similarity
    faiss.normalize_L2(query_vec)

    # Search the index
    scores, indices = _index.search(query_vec, k=top_k)

    # Build results list, filtering out any invalid indices
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        item = _metadata[idx].copy()
        item["score"] = float(score)
        results.append(item)

    return results


def get_by_name(name: str) -> dict | None:
    """
    Find a specific assessment by name (case-insensitive).
    Used for comparison queries like 'compare OPQ and GSA'.
    """
    name_lower = name.lower().strip()
    for item in _metadata:
        if name_lower in item["name"].lower():
            return item
    return None


def get_all_metadata() -> list[dict]:
    """Return the full catalog — used for comparison fallback."""
    return _metadata