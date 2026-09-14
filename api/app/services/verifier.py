# Ganymede API — Post-Retrieval Answer Verifier

"""NLI-based semantic verification for retrieval results.

Uses a 3-class NLI model (entailment/neutral/contradiction) to determine
whether a passage contains the answer to a question. Architecture decision: ADR 012.

The cross-encoder (ADR 011) was revoked: ms-marco is a relevance scorer, not an
answer-containment detector. NLI directly models the hypothesis→premise relation.
"""

from __future__ import annotations

import logging
import os
import time
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.retrieval import Citation

logger = logging.getLogger(__name__)

NLI_MODEL_NAME = os.environ.get(
    "NLI_MODEL",
    "roberta-large-mnli",
)
VERIFIER_THRESHOLD = float(os.environ.get("VERIFIER_THRESHOLD", "0.5"))

_nli_pipeline = None


def _get_nli_model():
    """Lazy-load and return the NLI model and tokenizer."""
    global _nli_pipeline
    if _nli_pipeline is None:
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            logger.info(f"Loading NLI model: {NLI_MODEL_NAME}")
            _nli_pipeline = (
                AutoTokenizer.from_pretrained(NLI_MODEL_NAME),
                AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME),
            )
            logger.info("NLI model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NLI model: {e}")
            raise
    return _nli_pipeline


def _make_hypothesis(question: str) -> str:
    """Construct a meta-level hypothesis for NLI verification.

    Rather than using the raw question as the hypothesis (which NLI models
    were not trained on), we assert: "The passage contains the answer to: [question]".
    This was empirically observed to produce better separation between
    answerable and answer-absent passages.
    """
    return f"The passage contains the answer to: {question}"


def verify_answer(question: str, passage: str) -> dict:
    """Verify whether a passage answers a question using NLI.

    Returns:
        dict with keys: decision (YES/NO/ERROR), score (entailment probability),
        latency_ms (inference time).
    """
    tokenizer, model = _get_nli_model()
    t0 = time.time()

    try:
        import torch
        import torch.nn.functional as F

        hypothesis = _make_hypothesis(question)
        inputs = tokenizer(
            passage, hypothesis,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        with torch.no_grad():
            logits = model(**inputs).logits  # shape: (1, 3)
            probs = F.softmax(logits, dim=-1).squeeze(0)

        # Model label mapping (DeBERTa-v3 MNLI): 0=entailment, 1=neutral, 2=contradiction
        id2label = model.config.id2label
        label_by_id = {int(k): v.lower() for k, v in id2label.items()}

        # Find entailment probability
        entailment_score = 0.0
        for idx, label_str in label_by_id.items():
            if "entail" in label_str:
                entailment_score = float(probs[idx])
                break
        if entailment_score == 0.0:
            raise RuntimeError(f"No entailment class found in model labels: {label_by_id}")

        label = "ENTAILMENT" if entailment_score >= VERIFIER_THRESHOLD else "NEUTRAL_OR_CONTRADICTION"
        score = entailment_score

    except Exception as e:
        logger.error(f"NLI verification failed: {e}")
        return {
            "decision": "ERROR",
            "score": 0.0,
            "latency_ms": (time.time() - t0) * 1000,
        }

    latency_ms = (time.time() - t0) * 1000

    decision = "YES" if score >= VERIFIER_THRESHOLD else "NO"
    return {
        "decision": decision,
        "score": score,
        "latency_ms": latency_ms,
    }


def verify_top_k(
    question: str,
    citations: List["Citation"],
    top_k_verify: int = 5,
) -> List["Citation"]:
    """Filter citations to only those whose NLI score >= threshold."""
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
    """Compatibility wrapper — NLI is already fast."""
    return verify_top_k(question, citations, top_k_verify=top_k_verify)


# Compatibility constant for tests
VERIFIER_MODEL = "roberta-large-mnli"
