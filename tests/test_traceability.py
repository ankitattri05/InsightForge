from engine.traceability import (
    extract_finding_ids,
    validate_finding_citations,
)


def test_extract_finding_ids():
    text = "The incident count is elevated [F-INCIDENT_COUNT]."
    assert extract_finding_ids(text) == ["F-INCIDENT_COUNT"]


def test_valid_finding_citation():
    text = "Incident volume increased [F-INCIDENT_COUNT]."

    findings = [
        {
            "finding_id": "F-INCIDENT_COUNT",
        }
    ]

    result = validate_finding_citations(text, findings)

    assert result["passed"] is True
    assert result["invalid_ids"] == []
    assert result["citation_coverage"] == 1.0


def test_invalid_finding_citation():
    text = "Incident volume increased [F-FAKE_METRIC]."

    findings = [
        {
            "finding_id": "F-INCIDENT_COUNT",
        }
    ]

    result = validate_finding_citations(text, findings)

    assert result["passed"] is False
    assert result["invalid_ids"] == ["F-FAKE_METRIC"]


def test_multiple_citations():
    text = (
        "Incidents increased [F-INCIDENT_COUNT], "
        "while SLA breaches remained elevated [F-SLA_BREACH_RATE]."
    )

    findings = [
        {"finding_id": "F-INCIDENT_COUNT"},
        {"finding_id": "F-SLA_BREACH_RATE"},
    ]

    result = validate_finding_citations(text, findings)

    assert result["passed"] is True
    assert result["citation_coverage"] == 1.0