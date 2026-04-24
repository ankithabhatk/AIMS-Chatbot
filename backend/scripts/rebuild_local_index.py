"""
Rebuild the FAISS index from local on-disk content only.

This script avoids network access by using:
- the existing stored FAISS metadata text
- the bundled official knowledge base
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Dict, Iterable, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embeddings.embed_pipeline import EmbeddingPipeline
from app.services.knowledge.official_knowledge import get_official_chunks
from app.services.retrieval.faiss_builder import build_faiss_index_from_embeddings
from app.services.taxonomy import (
    canonicalize_course,
    canonicalize_topic,
    mentioned_courses,
    mentioned_topics,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join("app", "data", "faiss_index")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")
TARGET_TOKENS = 120
OVERLAP_TOKENS = 24


def estimate_tokens(text: str) -> int:
    return max(len(text.split()), len(text) // 5)


def sentence_units(text: str) -> List[str]:
    parts = re.split(r"\n+|(?<=[.!?])\s+", text)
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return cleaned


def rechunk_text(text: str, target_tokens: int = TARGET_TOKENS, overlap_tokens: int = OVERLAP_TOKENS) -> List[str]:
    units = sentence_units(text)
    if not units:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = estimate_tokens(unit)
        if current and current_tokens + unit_tokens > target_tokens:
            chunks.append(" ".join(current).strip())
            overlap: List[str] = []
            overlap_total = 0
            for previous in reversed(current):
                overlap.insert(0, previous)
                overlap_total += estimate_tokens(previous)
                if overlap_total >= overlap_tokens:
                    break
            current = overlap + [unit]
            current_tokens = sum(estimate_tokens(part) for part in current)
        else:
            current.append(unit)
            current_tokens += unit_tokens

    if current:
        chunks.append(" ".join(current).strip())

    return [chunk for chunk in chunks if chunk and estimate_tokens(chunk) >= 40]


def infer_course(doc: Dict) -> str | None:
    heading_and_preview = f"{doc.get('heading', '')} {doc.get('content', '')[:240]}"
    explicit = mentioned_courses(heading_and_preview)
    if len(explicit) == 1:
        return next(iter(explicit))
    if len(explicit) > 1:
        return None
    return canonicalize_course(doc.get("heading", "")) or canonicalize_course(doc.get("content", "")[:200])


def infer_topic(doc: Dict) -> str | None:
    heading_and_preview = f"{doc.get('heading', '')} {doc.get('content', '')[:240]}"
    explicit = mentioned_topics(heading_and_preview)
    if len(explicit) == 1:
        return next(iter(explicit))
    return canonicalize_topic(doc.get("heading", "")) or canonicalize_topic(doc.get("content", "")[:200])


def load_seed_documents() -> List[Dict]:
    if not os.path.exists(METADATA_FILE):
        raise FileNotFoundError(f"Missing metadata file: {METADATA_FILE}")

    with open(METADATA_FILE, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    items = raw.get("metadata", raw) if isinstance(raw, dict) else raw
    documents: List[Dict] = []
    seen = set()
    grouped: Dict[tuple, Dict] = {}

    for item in items:
        content = item.get("full_text") or item.get("text", "")
        if not content:
            continue
        group_key = (
            item.get("url", ""),
            item.get("heading", "Untitled"),
            item.get("source", "web"),
        )
        grouped.setdefault(
            group_key,
            {
                "segments": [],
                "url": item.get("url", ""),
                "heading": item.get("heading", "Untitled"),
                "source": item.get("source", "web"),
                "priority": float(item.get("priority", 1.0)),
                "course": item.get("course"),
                "category": item.get("category"),
            },
        )
        grouped[group_key]["segments"].append(content.strip())

    for group in grouped.values():
        ordered_segments: List[str] = []
        local_seen = set()
        for segment in group.pop("segments", []):
            fingerprint = segment[:200]
            if fingerprint in local_seen:
                continue
            local_seen.add(fingerprint)
            ordered_segments.append(segment)

        content = "\n".join(ordered_segments).strip()
        key = (group.get("url", ""), group.get("heading", ""), content[:200])
        if key in seen:
            continue
        seen.add(key)
        documents.append({**group, "content": content})

    for item in get_official_chunks():
        key = (item.get("url", ""), item.get("title", ""), item.get("content", "")[:200])
        if key in seen:
            continue
        seen.add(key)
        documents.append(
            {
                "content": item.get("content", "").strip(),
                "url": item.get("url", ""),
                "heading": item.get("title", "Official Knowledge"),
                "source": "official",
                "priority": 2.0,
                "course": None,
                "category": item.get("category"),
            }
        )

    return documents


def build_chunks(documents: Iterable[Dict]) -> List[Dict]:
    chunks: List[Dict] = []
    for document in documents:
        split_chunks = rechunk_text(document["content"])
        course = infer_course(document)
        topic = infer_topic(document)

        for idx, chunk_text in enumerate(split_chunks):
            chunk_explicit_courses = mentioned_courses(chunk_text[:260])
            if len(chunk_explicit_courses) == 1:
                chunk_course = next(iter(chunk_explicit_courses))
            elif len(chunk_explicit_courses) > 1:
                chunk_course = None
            else:
                chunk_course = canonicalize_course(chunk_text[:220]) or course

            chunk_explicit_topics = mentioned_topics(chunk_text[:260])
            if len(chunk_explicit_topics) == 1:
                chunk_topic = next(iter(chunk_explicit_topics))
            else:
                chunk_topic = canonicalize_topic(chunk_text[:220]) or canonicalize_topic(document["heading"]) or topic

            importance = 1.4 if document["source"] == "official" else 1.0
            if chunk_topic in {"fees", "placements", "hostel", "admission"}:
                importance += 0.2

            chunks.append(
                {
                    "content": chunk_text,
                    "url": document["url"],
                    "heading": document["heading"],
                    "chunk_index": idx,
                    "tokens": estimate_tokens(chunk_text),
                    "course": chunk_course,
                    "category": chunk_topic,
                    "source": document["source"],
                    "priority": float(document["priority"]),
                    "importance": round(importance, 2),
                }
            )

    return chunks


def main() -> int:
    logger.info("Loading local knowledge sources...")
    documents = load_seed_documents()
    logger.info("Loaded %s seed documents", len(documents))

    chunks = build_chunks(documents)
    logger.info("Built %s offline chunks", len(chunks))

    pipeline = EmbeddingPipeline()
    embeddings = pipeline.embed_batch([chunk["content"] for chunk in chunks]).tolist()
    metadata = [
        {
            "text": chunk["content"],
            "url": chunk["url"],
            "heading": chunk["heading"],
            "chunk_index": chunk["chunk_index"],
            "tokens": chunk["tokens"],
            "source": chunk["source"],
            "priority": chunk["priority"],
            "importance": chunk["importance"],
            "course": chunk["course"],
            "category": chunk["category"],
        }
        for chunk in chunks
    ]
    doc_ids = [
        f"{chunk['url']}#{chunk['heading']}#{chunk['chunk_index']}"
        for chunk in chunks
    ]

    builder = build_faiss_index_from_embeddings(
        embeddings=embeddings,
        documents=metadata,
        doc_ids=doc_ids,
    )
    logger.info("Rebuilt local FAISS index at %s", builder.index_path)
    logger.info("Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
