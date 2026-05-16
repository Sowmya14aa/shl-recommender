"""
build_index.py — Converts catalog.json into a FAISS vector index.

Run ONCE after scraping:
    python data/build_index.py

Outputs into data/faiss_index/:
    index.faiss   — the vector index
    metadata.json — assessment details matched by position to index
"""

import json
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "catalog.json")
INDEX_DIR    = os.path.join(os.path.dirname(__file__), "faiss_index")
INDEX_PATH   = os.path.join(INDEX_DIR, "index.faiss")
META_PATH    = os.path.join(INDEX_DIR, "metadata.json")

MODEL_NAME = "all-MiniLM-L6-v2"


def build_search_text(item: dict) -> str:
    """
    Combine all fields into one string for embedding.
    We include name, type, description, and job levels so the
    vector captures meaning from every angle.
    """
    parts = [
        item.get("name", ""),
        item.get("test_type", ""),
        item.get("description", ""),
        item.get("job_levels", ""),
    ]
    return " | ".join(p for p in parts if p.strip())


def main():
    print("Building FAISS vector index from SHL catalog")
    print("=" * 60)

    # Step 1: Load catalog
    print("\n1. Loading catalog.json...")
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)
    print(f"   Loaded {len(catalog)} assessments")

    # Step 2: Load embedding model
    # all-MiniLM-L6-v2 is small (80MB), fast, good for semantic search
    # First run downloads from HuggingFace, then cached locally
    print(f"\n2. Loading embedding model: {MODEL_NAME}")
    print("   First run downloads ~80MB — please wait...")
    model = SentenceTransformer(MODEL_NAME)
    print("   Model ready!")

    # Step 3: Build search texts
    print("\n3. Building search texts...")
    texts = [build_search_text(item) for item in catalog]
    print(f"   Sample: {texts[1][:100]}...")

    # Step 4: Generate embeddings
    # Each text becomes a 384-dimensional vector
    print(f"\n4. Generating embeddings for {len(texts)} assessments...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    print(f"   Shape: {embeddings.shape}")

    # Step 5: Normalize for cosine similarity
    # After normalization, dot product = cosine similarity
    faiss.normalize_L2(embeddings)

    # Step 6: Build FAISS index
    print("\n5. Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    print(f"   Index contains {index.ntotal} vectors")

    # Step 7: Save everything
    print("\n6. Saving files...")
    os.makedirs(INDEX_DIR, exist_ok=True)

    faiss.write_index(index, INDEX_PATH)
    print(f"   Saved index.faiss")

    metadata = [
        {
            "name"           : item["name"],
            "url"            : item["url"],
            "test_type"      : item["test_type"],
            "test_type_codes": item.get("test_type_codes", ""),
            "description"    : item["description"],
            "duration"       : item.get("duration", ""),
            "job_levels"     : item.get("job_levels", ""),
            "remote_testing" : item.get("remote_testing", ""),
            "adaptive_irt"   : item.get("adaptive_irt", ""),
        }
        for item in catalog
    ]
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"   Saved metadata.json")

    # Step 8: Sanity checks
    print("\n7. Sanity checks...")
    test_queries = [
        "Java developer programming test",
        "personality test for managers",
        "numerical reasoning ability",
    ]
    for query in test_queries:
        vec = model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(vec)
        scores, indices = index.search(vec, k=3)
        print(f"\n   Query: '{query}'")
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
            print(f"   {rank}. {metadata[idx]['name'][:50]} (score: {score:.3f})")

    print("\nDone! Run the app next.")


if __name__ == "__main__":
    main()