"""
Deterministic causal-language linter.

Flags unsupported causal claims in LLM-generated business narratives.

No LLM.
No SQL.
No inference.
"""

import re


BANNED_CAUSAL_PATTERNS = [
    r"\bbecause\b",
    r"\bcaused\b",
    r"\bcauses\b",
    r"\bcausing\b",
    r"\bled to\b",
    r"\bleads to\b",
    r"\bresulted in\b",
    r"\bresults in\b",
    r"\bresulting in\b",
    r"\bdue to\b",
    r"\bdriven by\b",
    r"\bwas caused by\b",
]


def find_causal_language(text: str) -> list[str]:
    """
    Return unsupported causal phrases found in the text.
    """
    found = []

    denial_patterns = [
        r"\bdoes not (establish|prove|indicate|confirm)(?: that)?\b[^.]*{pattern}",
        r"\bdo not (explain|establish|prove|indicate|confirm)(?: why| that)?\b[^.]*{pattern}",
        r"\bdoes not explain(?: why| how)?\b[^.]*{pattern}",
        r"\bnot enough evidence to\b[^.]*{pattern}",
        r"\bnot what\b[^.]*{pattern}",
    ]

    for pattern in BANNED_CAUSAL_PATTERNS:
        exempted = any(
            re.search(
                denial_pattern.format(pattern=pattern),
                text,
                flags=re.IGNORECASE,
            )
            for denial_pattern in denial_patterns
        )

        if exempted:
            continue

        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        if matches:
            found.append(matches[0])

    return sorted(set(found), key=str.lower)


def lint_causal_language(text: str) -> dict:
    """
    Validate narrator output for unsupported causal language.
    """
    violations = find_causal_language(text)

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "violation_count": len(violations),
    }

