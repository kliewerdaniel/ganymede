# Ganymede API — Input Sanitizer & Prompt Injection Detection

import re
from typing import Optional

# Patterns that suggest prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions?",
    r"ignore\s+all\s+prior\s+instructions?",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"system\s+prompt",
    r"new\s+persona",
    r"disregard\s+(all|your)\s+",
    r"forget\s+(all|your|previous)\s+",
    r"pretend\s+(to\s+be|you\s+are)\s+",
    r"act\s+as\s+(a|an)\s+",
    r"do\s+not\s+(follow|obey|adhere)\s+",
    r"override\s+(all|your)\s+",
    r"jailbreak",
    r"mode\s*:\s*(developer|admin|root|unrestricted)",
    r"<\s*/\s*instruction\s*>",
    r"<\s*instruction\s*>",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def sanitize_query(text: str) -> str:
    """Sanitize user query input.

    - Strips control characters
    - Limits length to 10,000 chars
    - Normalizes whitespace
    """
    if not text:
        return ""

    # Remove control characters (except newline, tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Limit length
    if len(text) > 10000:
        text = text[:10000]

    return text


def sanitize_passage(text: str) -> str:
    """Sanitize passage text from documents.

    - Strips control characters
    - Limits length to 50,000 chars
    """
    if not text:
        return ""

    # Remove control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Limit length
    if len(text) > 50000:
        text = text[:50000]

    return text


def detect_injection(text: str) -> Optional[str]:
    """Detect prompt injection patterns in text.

    Returns:
        The matched pattern string if detected, None otherwise.
    """
    if not text:
        return None

    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)

    return None


def is_suspicious_document(text: str) -> bool:
    """Check if document text contains suspicious injection patterns."""
    if not text:
        return False

    # Check for injection patterns that target LLMs
    injection_indicators = [
        r"ignore\s+(previous|all|above)\s+(instructions?|prompts?)",
        r"you\s+are\s+now",
        r"new\s+instructions?:",
        r"system:\s*",
        r"<\s*script",
    ]

    for pattern in injection_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False
