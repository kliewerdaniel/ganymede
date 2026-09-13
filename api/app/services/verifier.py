# Ganymede API — Post-Retrieval Answer Verifier

"""Local LLM-based answer verification for retrieval results.

Identifies whether retrieved passages actually answer the question,
filtering out spurious citations on unanswerable queries.

Uses qwen3:4b via Ollama (local-only, port 11434). No external API calls.
"""

from __future__ import annotations

import json
import logging
import time
from typing import List, Optional, TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.services.retrieval import Citation

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434"
VERIFIER_MODEL = "qwen3:4b"
VERIFIER_PROMPT_VERSION = "1.0.0"

# Shared Ollama client — reuse across calls, timeout 60s
_ollama_client: Optional[httpx.Client] = None


def _get_client() -> httpx.Client:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = httpx.Client(base_url=OLLAMA_URL, timeout=60.0)
    return _ollama_client


def _load_verifier_prompt() -> str:
    import os
    # verifier.py lives at api/app/services/verifier.py — 4 levels up to repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    prompt_path = os.path.join(repo_root, "docs", "specification", "verifier-prompt.md")
    try:
        with open(prompt_path) as f:
            content = f.read()
        system_start = content.index("You are a precision answer verifier")
        input_start = content.index("## Input format")
        system_section = content[system_start:input_start].strip()
        return system_section
    except Exception as e:
        logger.error(f"Failed to load verifier prompt: {e}")
        return (
            "You are a precision answer verifier for a legal document retrieval system. "
            "Given a question and a retrieved passage, determine whether the passage "
            "contains information that answers the question. Reply with exactly one line: "
            "YES and quote the exact supporting span, or NO. "
            "If the passage mentions the topic but does not contain the specific fact asked for, reply NO. "
            "If the passage is too short (fewer than 8 words), reply NO. "
            "Do not use outside knowledge. Do not explain your reasoning."
        )


def verify_answer(question: str, passage: str, client: Optional[httpx.Client] = None) -> dict:
    """Ask the LLM whether a passage answers a question.

    Uses Ollama /api/generate endpoint (qwen3:4b produces empty content
    on /api/chat — only thinking is populated. /api/generate returns
    visible content).
    """
    prompt_text = _load_verifier_prompt()
    payload = {
        "model": VERIFIER_MODEL,
        "prompt": prompt_text + "\n\nQuestion: " + question + "\nPassage: " + passage,
        "stream": False,
    }

    c = client or _get_client()
    t0 = time.time()
    try:
        resp = c.post("/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama verifier call failed: {e}")
        return {
            "decision": "ERROR",
            "quote": None,
            "latency_ms": (time.time() - t0) * 1000,
            "raw_response": f"ERROR: {e}",
        }
    latency_ms = (time.time() - t0) * 1000

    # Parse: expect exactly "YES: <quote>" or "NO"
    if raw.upper().startswith("YES"):
        # Extract the quote after "YES:"
        colon_idx = raw.index(":")
        quote = raw[colon_idx + 1:].strip()
        return {
            "decision": "YES",
            "quote": quote,
            "latency_ms": latency_ms,
            "raw_response": raw,
        }
    else:
        return {
            "decision": "NO",
            "quote": None,
            "latency_ms": latency_ms,
            "raw_response": raw,
        }


def verify_top_k(
    question: str,
    citations: List["Citation"],
    client: Optional[httpx.Client] = None,
    top_k_verify: int = 5,
) -> List["Citation"]:
    """Filter citations to only those the LLM verifier confirms answer the question.

    Args:
        question: the user's question
        citations: retrieved Citation objects (already ranked)
        client: optional shared httpx client
        top_k_verify: how many of the top citations to verify

    Returns:
        List of Citation objects that passed verification (YES decision).
        If none pass, returns empty list.
    """
    from app.services.retrieval import Citation as CitationType

    to_verify = citations[:top_k_verify]
    verified: List[CitationType] = []

    for cite in to_verify:
        result = verify_answer(question, cite.quoted_text, client=client)
        if result["decision"] == "YES":
            # Attach verifier metadata to the citation's retrieval_scores
            cite.retrieval_scores["verifier_decision"] = "YES"
            cite.retrieval_scores["verifier_quote"] = result["quote"]
            cite.retrieval_scores["verifier_latency_ms"] = result["latency_ms"]
            verified.append(cite)

    return verified


def verify_batch_latency(
    questions: List[tuple],
    get_citations_fn,
    client: Optional[httpx.Client] = None,
) -> dict:
    """Measure verifier latency over a batch of questions.

    Args:
        questions: list of (q_id, question_text) tuples
        get_citations_fn: function(question_text) -> list of Citations
        client: optional shared httpx client

    Returns:
        dict with per-question latency and aggregate stats.
    """
    latencies = []
    results = []

    for q_id, question in questions:
        citations = get_citations_fn(question)
        t0 = time.time()

        # Verify each citation
        for cite in citations[:5]:
            verify_answer(question, cite.quoted_text, client=client)

        latency_ms = (time.time() - t0) * 1000
        latencies.append(latency_ms)
        results.append({"q_id": q_id, "latency_ms": latency_ms, "n_citations": len(citations)})

    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[len(latencies_sorted) // 2]
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]

    return {
        "per_question": results,
        "p50_ms": p50,
        "p95_ms": p95,
        "mean_ms": sum(latencies) / len(latencies),
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "n_queries": len(latencies),
    }


# Convenience: verify citations from the retrieve() output directly
def filter_verified_citations(
    question: str,
    citations: List["Citation"],
    client: Optional[httpx.Client] = None,
) -> List["Citation"]:
    """Convenience wrapper: verify top-5 citations and return only YES ones."""
    return verify_top_k(question, citations, client=client, top_k_verify=5)
