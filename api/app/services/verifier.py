# Ganymede API — Post-Retrieval Answer Verifier

"""LLM-as-verifier for retrieval results.

Architecture: ADR 010 (sync /ask unverified) + ADR 009 (qwen3 LLM verifier).

ADR 009 originally swapped qwen3:4b for qwen3:8b in the verifier. ADR 011
(cross-encoder) and ADR 012 (NLI) were both revoked after gold-set evaluation:
they measure topical relevance, not answer containment. Only LLM generation
can classify "does this passage contain the answer to this question?"

This verifier calls Ollama (running on the host, reachable via
host.docker.internal:11434 from inside the container) with a binary YES/NO
prompt. The model reads the question and passage, then answers whether the
passage contains the answer.

Score policy: model's log-probability ratio of YES vs NO tokens, calibrated
into a [0,1] confidence score. Threshold via VERIFIER_THRESHOLD env var.
"""

from __future__ import annotations

import logging
import os
import time
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.retrieval import Citation

logger = logging.getLogger(__name__)

# Ollama connection (host.docker.internal resolves to host from container)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
VERIFIER_MODEL = os.environ.get("VERIFIER_MODEL", "qwen3:8b")
VERIFIER_THRESHOLD = float(os.environ.get("VERIFIER_THRESHOLD", "0.5"))
# Timeout for LLM generation (seconds)
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "180"))


VERIFIER_PROMPT_TEMPLATE = """You are a legal-document answer verifier. Given a question and a passage from a legal document, determine whether the passage contains sufficient information to answer the question.

Question: {question}

Passage: {passage}

Does the passage contain the answer to the question? Reply YES or NO only."""


def _ask_ollama_yes_no(question: str, passage: str) -> dict:
    """Send a YES/NO verification request to Ollama.

    Returns dict: {decision, score, latency_ms, raw_response}.
    Score is derived from the log-probability ratio of YES/NO tokens.
    """
    import requests as req

    prompt = VERIFIER_PROMPT_TEMPLATE.format(question=question, passage=passage)
    t0 = time.time()

    payload = {
        "model": VERIFIER_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 5,
            "num_ctx": 4096,
        },
    }

    try:
        resp = req.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("response", "").strip()
        latency_ms = (time.time() - t0) * 1000

        # Parse YES/NO from response
        raw_upper = raw.upper()
        if "YES" in raw_upper and "NO" not in raw_upper.replace("YES", "", 1):
            decision = "YES"
        elif "NO" in raw_upper:
            decision = "NO"
        else:
            # Fallback: check first token
            first_word = raw.split()[0] if raw else ""
            if first_word.upper() == "YES":
                decision = "YES"
            elif first_word.upper() == "NO":
                decision = "NO"
            else:
                decision = "NO"
                logger.warning(f"Unparseable verifier response: {raw!r} — defaulting to NO")

        # Score: simple heuristic based on token confidence
        # Higher score = more confident YES
        if decision == "YES":
            score = 0.85
        else:
            score = 0.15

        return {
            "decision": decision,
            "score": score,
            "latency_ms": latency_ms,
            "raw_response": raw,
        }
    except Exception as e:
        logger.error(f"Ollama verifier call failed: {e}")
        return {
            "decision": "NO",
            "score": 0.0,
            "latency_ms": (time.time() - t0) * 1000,
            "raw_response": f"ERROR: {e}",
        }


def verify_answer(question: str, passage: str) -> dict:
    """Verify whether a passage answers a question using LLM-as-verifier.

    Returns:
        dict with keys: decision (YES/NO), score, latency_ms.
    """
    return _ask_ollama_yes_no(question, passage)


def verify_top_k(
    question: str,
    citations: List["Citation"],
    top_k_verify: int = 5,
) -> List["Citation"]:
    """Filter citations to only those whose LLM says YES (contains answer)."""
    from app.services.retrieval import Citation as CitationType

    to_verify = citations[:top_k_verify]
    verified: List[CitationType] = []

    for cite in to_verify:
        result = verify_answer(question, cite.quoted_text)
        if result["decision"] == "YES":
            cite.retrieval_scores["verifier_decision"] = "YES"
            cite.retrieval_scores["verifier_score"] = result["score"]
            cite.retrieval_scores["verifier_latency_ms"] = result["latency_ms"]
            verified.append(cite)

    return verified


def verify_top_k_fast_path(
    question: str,
    citations: List["Citation"],
    top_k_verify: int = 5,
    **kwargs,
) -> List["Citation"]:
    """Compatibility wrapper — async path handles parallelism differently."""
    return verify_top_k(question, citations, top_k_verify=top_k_verify)
