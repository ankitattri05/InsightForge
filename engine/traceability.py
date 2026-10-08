"""
Deterministic finding traceability checks.

Verifies that Finding IDs referenced by the narrator
actually exist in the verified findings supplied to it.

No LLM.
No SQL.
No inference.
"""

import re


FINDING_ID_PATTERN = re.compile(r"\bF-[A-Z0-9_]+\b")


def extract_finding_ids(text: str) -> list[str]:
    """Extract Finding IDs cited in narrator output."""
    return sorted(set(FINDING_ID_PATTERN.findall(text)))


def validate_finding_citations(
    text: str,
    verified_findings: list[dict],
) -> dict:
    """
    Verify that every cited Finding ID exists
    in the verified findings.
    """
    cited_ids = extract_finding_ids(text)

    valid_ids = {
        finding["finding_id"]
        for finding in verified_findings
        if "finding_id" in finding
    }

    invalid_ids = [
        finding_id
        for finding_id in cited_ids
        if finding_id not in valid_ids
    ]

    return {
        "passed": not invalid_ids,
        "cited_ids": cited_ids,
        "valid_ids": sorted(valid_ids),
        "invalid_ids": invalid_ids,
        "citation_coverage": (
            len([fid for fid in cited_ids if fid in valid_ids])
            / len(cited_ids)
            if cited_ids
            else 1.0
        ),
    }

def validate_finding_interpretations(
    findings: list[dict],
) -> dict:
    """Validate deterministic business interpretations before narration."""
    errors = []

    for finding in findings:
        finding_id = finding.get("finding_id", "UNKNOWN")

        for field in ("business_meaning", "interpretation"):
            value = finding.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"{finding_id}: missing or invalid {field}"
                )

        if finding.get("comparison") is not None:
            comparison_interpretation = finding.get(
                "comparison_interpretation"
            )

            if not isinstance(comparison_interpretation, dict):
                errors.append(
                    f"{finding_id}: missing comparison interpretation"
                )
            else:
                classification = comparison_interpretation.get(
                    "classification"
                )
                meaning = comparison_interpretation.get("meaning")

                if not isinstance(classification, str) or classification in (
                    "",
                    "unclassified",
                ):
                    errors.append(
                        f"{finding_id}: undefined comparison classification"
                    )

                if not isinstance(meaning, str) or not meaning.strip():
                    errors.append(
                        f"{finding_id}: missing comparison meaning"
                    )

    return {
        "passed": not errors,
        "errors": errors,
    }