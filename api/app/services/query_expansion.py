"""Query expansion service for Ganymede retrieval pipeline.

Provides targeted query expansion that combines:
1. Date normalization (for date-related questions)
2. Legal-term synonym expansion (for questions containing legal terms)

This is NOT the over-expanded "combined" variant from the expansion benchmark
(which applied ALL expansions to ALL queries). This is a TARGETED expansion
that only applies expansions relevant to the specific question content.

Design:
- Apply date normalization ONLY for questions referencing dates
- Apply legal-term synonyms ONLY for terms actually present in the question
- Prefer legal synonyms over date normalization when both apply (avoids
  verbose query stacking that dilutes RRF scores)
"""

import re

# Date-related keywords that trigger date normalization
DATE_KEYWORDS = {"date", "when", "what date", "on what date", "timeline", "chronolog"}

# Legal-term synonym mappings (inline replacement)
# Only applied if the term is present in the question
LEGAL_SYNONYMS = [
    ("breach", "default breach"),
    ("notice", "notice demand"),
    ("received notice", "served with notice"),
    ("contract price", "amount total balance sum"),
    ("invoice", "invoice billing statement"),
    ("filing", "filing court docket"),
    ("deposition", "deposition transcript"),
    ("document", "document filing record"),
    ("settlement", "settlement resolution"),
    ("damages", "damages compensation award"),
    ("termination", "termination end expiration"),
    ("amendment", "amendment modification revision"),
    ("complaint", "complaint petition suit"),
    ("answer", "answer response reply"),
    ("default", "default breach failure to perform"),
    ("cure period", "cure period grace period remediation"),
    ("jurisdiction", "jurisdiction venue forum"),
    ("warranty", "warranty guarantee assurance"),
    ("confidentiality", "confidentiality non-disclosure"),
    ("exhibit", "exhibit attachment appendix"),
    ("expert", "expert specialist consultant"),
    ("witness", "witness testifier deponent"),
    ("non-compete", "non-compete non-competition restraint"),
    ("indemnitor", "indemnitor indemnifier guarantor"),
]


def _is_date_question(question: str) -> bool:
    """Check if the question references a date or temporal ordering."""
    q = question.lower()
    return any(kw in q for kw in DATE_KEYWORDS)


def _has_legal_terms(question: str) -> bool:
    """Check if the question contains any legal terms from the mapping."""
    q = question.lower()
    return any(term in q for term, _ in LEGAL_SYNONYMS)


def expand_query(query: str) -> str:
    """Apply targeted query expansion based on question content.

    Strategy:
    1. If the question contains legal terms, apply legal synonyms (inline replacement).
    2. If the question is a date question AND has no legal terms, apply date normalization.
    3. If the question has both, prefer legal synonyms only (avoids verbose stacking).
    4. Otherwise, return the query unchanged.

    This avoids the over-expansion problem: the "combined" variant from the
    benchmark applied ALL expansions to ALL queries, creating verbose queries
    that diluted RRF scores.
    """
    q = query

    has_legal = _has_legal_terms(query)
    is_date = _is_date_question(query)

    if has_legal:
        # Apply legal-term synonyms (inline replacement)
        for term, replacement in LEGAL_SYNONYMS:
            if term in q.lower():
                q = q.replace(term, replacement)
    elif is_date:
        # Apply date normalization only if no legal terms present
        q = q.replace("date", "DATE date").replace("when", "DATE when")

    return q


def expand_query_with_fallback(query: str) -> list:
    """Generate multiple query variants for fusion-based retrieval.

    Returns a list of query strings: [original, expanded, date_normalized].
    The retrieval pipeline can run all variants and fuse results via RRF.
    """
    variants = [query]

    expanded = expand_query(query)
    if expanded != query:
        variants.append(expanded)

    # Also add date-normalized variant for date questions (if not already added)
    if _is_date_question(query) and not _has_legal_terms(query):
        date_variant = query.replace("date", "DATE date").replace("when", "DATE when")
        if date_variant != expanded:
            variants.append(date_variant)

    return variants
