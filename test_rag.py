"""
Test Suite & Validation Script for Computer & Device Support Assistant RAG Pipeline
Runs checks on document loading, chunking, FAISS retrieval, and test questions evaluation.
"""

import os
import csv
import glob
import re
import sys
from typing import List, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(os.path.dirname(__file__), "test_questions.csv")
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_THRESHOLD = 0.35
TOP_K = 4


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_documents(data_path: str) -> List[Dict[str, str]]:
    if not os.path.exists(data_path):
        return []
    file_paths = glob.glob(os.path.join(data_path, "*.txt"))
    documents = []
    for file_path in sorted(file_paths):
        filename = os.path.basename(file_path)
        content = ""
        for encoding in ["utf-8", "utf-8-sig", "tis-620", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except Exception:
                continue
        cleaned = clean_text(content)
        if cleaned:
            documents.append({"source": filename, "text": cleaned})
    return documents


def chunk_text(documents: List[Dict[str, str]], chunk_size: int = 650, overlap: int = 120) -> List[Dict[str, Any]]:
    chunks = []
    chunk_counter = 0
    for doc in documents:
        source = doc["source"]
        text = doc["text"]
        text_len = len(text)
        if text_len <= chunk_size:
            chunk_counter += 1
            chunks.append({"source": source, "chunk_id": chunk_counter, "text": text})
            continue

        start = 0
        while start < text_len:
            end = start + chunk_size
            chunk_slice = text[start:end]
            if end < text_len:
                last_newline = chunk_slice.rfind("\n")
                if last_newline != -1 and last_newline > chunk_size * 0.5:
                    chunk_slice = text[start : start + last_newline]
                    end = start + last_newline
                else:
                    last_space = chunk_slice.rfind(" ")
                    if last_space != -1 and last_space > chunk_size * 0.5:
                        chunk_slice = text[start : start + last_space]
                        end = start + last_space

            cleaned_chunk = chunk_slice.strip()
            if cleaned_chunk:
                chunk_counter += 1
                chunks.append({"source": source, "chunk_id": chunk_counter, "text": cleaned_chunk})

            start = end - overlap
            if start >= text_len - overlap:
                break
    return chunks


def load_test_questions(csv_path: str) -> List[Dict[str, str]]:
    questions = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row)
    return questions


def run_pipeline_validation():
    print("=" * 70)
    print("🔍 Testing Document Loading & Chunking")
    print("=" * 70)

    docs = load_documents(DATA_DIR)
    print(f"✅ Loaded {len(docs)} documents from '{DATA_DIR}'")
    assert len(docs) >= 12, f"Expected at least 12 documents, got {len(docs)}"

    for doc in docs:
        print(f"   - {doc['source']}: {len(doc['text'])} characters")

    chunks = chunk_text(docs)
    print(f"\n✅ Total Chunks Generated: {len(chunks)}")
    assert len(chunks) > 0, "No chunks generated"

    test_cases = load_test_questions(CSV_PATH)
    print(f"\n✅ Loaded {len(test_cases)} test cases from '{CSV_PATH}'")
    assert len(test_cases) >= 10, f"Expected at least 10 test cases, got {len(test_cases)}"

    # Check dependencies for embedding & FAISS testing
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np
    except ImportError as e:
        print(f"\n⚠️ Note: {e}. Skipping live vector inference tests.")
        print("💡 When Python dependencies are installed, full retrieval benchmarks will run.")
        print("\n🎉 Basic structure and data integrity tests PASSED!")
        return

    print("\n" + "=" * 70)
    print("⚡ Loading Embedding Model & Building FAISS Vector Index")
    print("=" * 70)
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    print(f"✅ FAISS Index FlatIP created with dimension {dimension} and {index.ntotal} vectors.")

    print("\n" + "=" * 70)
    print("🎯 Evaluating Test Questions against Vector Retrieval & Threshold")
    print("=" * 70)

    passed_count = 0
    for idx, tc in enumerate(test_cases, 1):
        q = tc["question"]
        expected_src = tc.get("expected_source", "")
        cat = tc.get("category", "")

        q_vec = model.encode([q], normalize_embeddings=True)
        q_vec = np.array(q_vec, dtype=np.float32)
        scores, indices = index.search(q_vec, TOP_K)

        top_score = float(scores[0][0])
        top_chunk_idx = indices[0][0]
        retrieved_src = chunks[top_chunk_idx]["source"] if top_chunk_idx != -1 else "NONE"

        is_relevant = top_score >= SIMILARITY_THRESHOLD

        if expected_src == "NO_MATCH":
            passed = not is_relevant
            status = "PASSED (Rejected as Out-of-Domain)" if passed else "FAILED (Should be Rejected)"
        else:
            passed = is_relevant and (retrieved_src == expected_src)
            status = f"PASSED (Retrieved {retrieved_src})" if passed else f"FAILED (Got {retrieved_src}, Score: {top_score:.2f})"

        if passed:
            passed_count += 1

        print(f"[{idx:02d}] Question: {q}")
        print(f"     Top Score: {top_score:.4f} | Threshold: {SIMILARITY_THRESHOLD} | Relevant: {is_relevant}")
        print(f"     Expected: {expected_src} | Retrieved: {retrieved_src}")
        print(f"     Result: {status}\n")

    accuracy = (passed_count / len(test_cases)) * 100
    print("=" * 70)
    print(f"📊 Test Summary: {passed_count}/{len(test_cases)} Passed ({accuracy:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_validation()
