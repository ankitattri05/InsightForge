
"""Evaluate committed vs current SLA interpretation.

Run: python -m eval.evaluate_sla_interpretation
Scores decision guidance, not operational outcomes.
"""
from __future__ import annotations

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "engine" / "interpreter_telecom.py"


def load_interpreter(source: str):
    tree = ast.parse(source)
    node = next(
        item for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "_interpret_sla_diagnostics"
    )
    namespace = {}
    isolated = ast.Module(body=[node], type_ignores=[])
    exec(compile(isolated, "<isolated_interpreter>", "exec"), namespace)
    return namespace["_interpret_sla_diagnostics"]


def baseline_source() -> str:
    return subprocess.run(
        ["git", "show", "HEAD:engine/interpreter_telecom.py"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        check=True,
    ).stdout


def fixture() -> dict:
    fault = {
        "category": "Optical Network", "display": "19.74%",
        "value": 0.1974, "overall_rate": 0.0999,
        "excess_vs_overall_pp": 9.75, "n": 6425,
        "minimum_n_met": True, "observed_breaches": 1268,
        "benchmark_breaches": 642, "excess_breaches": 626,
        "incident_share": 0.257, "breach_share": 0.507,
        "cost": 1546035350.92, "cost_share": 0.498,
        "breach_concentration": 1.98, "cost_concentration": 1.94,
    }
    vendor = {
        "category": "Vendor A", "display": "15.20%",
        "value": 0.152, "overall_rate": 0.0999,
        "n": 1200, "minimum_n_met": True,
        "observed_breaches": 182, "excess_breaches": 62,
    }
    return {
        "top_fault": [fault], "top_vendor": [vendor],
        "excess_breach_fault": [
            {"category": "Optical Network", "excess_breaches": 626}
        ],
        "excess_breach_vendor": [
            {"category": "Vendor A", "excess_breaches": 62}
        ],
        "excess_breach_state": [
            {"category": "State X", "excess_breaches": 100}
        ],
    }


FAULT_RULES = [
    ("Causality boundary",
     lambda t: "does not establish root cause or causality" in t),
    ("Investigation compares relevant dimensions",
     lambda t: "next step:" in t and all(
         x in t for x in ("site", "vendor", "severity", "fault")
     )),
    ("Pre-intervention baseline",
     lambda t: "pre-intervention breach-rate baseline" in t),
    ("Comparable measurement windows",
     lambda t: "comparable reporting windows" in t),
    ("Target and operational guardrails",
     lambda t: "target must be agreed before the intervention" in t
     and all(x in t for x in ("incident volume", "resolution time", "guardrails"))),
    ("Financial integrity",
     lambda t: "not estimates of preventable incidents or recoverable savings" in t),
]

VENDOR_RULES = [
    ("Reports observed vendor breach rate",
     lambda t: "highest observed sla breach rate" in t),
    ("Includes sample and observed breaches",
     lambda t: "incidents" in t and "observed breaches" in t),
    ("Explicit non-causality boundary",
     lambda t: "not proof" in t and "caused the breaches" in t),
    ("Action and measurement guidance",
     lambda t: all(x in t for x in (
         "next step:", "fault category", "pre-intervention",
         "comparable reporting windows", "guardrails"
     ))),
]


def report(label: str, text: str, rules: list) -> int:
    print(f"\n{label}")
    score = 0
    for name, check in rules:
        passed = bool(check(text.lower()))
        score += int(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"  Score: {score}/{len(rules)}")
    return score


def main() -> int:
    baseline = load_interpreter(baseline_source())
    current = load_interpreter(SOURCE.read_text(encoding="utf-8"))
    data = fixture()

    old = baseline(data)
    new = current(data)

    print("INSIGHTFORGE SLA INTERPRETATION EVALUATION")
    print("Baseline: committed HEAD | Candidate: working tree")
    before = report("BASELINE — fault interpretation",
                    old.get("meaning", ""), FAULT_RULES)
    after = report("CURRENT — fault interpretation",
                   new.get("meaning", ""), FAULT_RULES)
    print(f"\nFAULT CHANGE: {after - before:+d} points "
          f"({before}/{len(FAULT_RULES)} -> {after}/{len(FAULT_RULES)})")

    vendor_score = report("CURRENT — vendor interpretation",
                          new.get("vendor_meaning", ""), VENDOR_RULES)

    print("\nEDGE-CASE CHECKS")
    checks = [
        ("No fault diagnostic returns unavailable",
         current({"top_fault": []}).get("status") == "unavailable"),
        ("Fault below minimum sample returns unavailable",
         current({"top_fault": [{"minimum_n_met": False}]}).get("status")
         == "unavailable"),
    ]
    low_sample = fixture()
    low_sample["top_vendor"][0]["minimum_n_met"] = False
    low_sample_result = current(low_sample)
    checks.append((
        "Vendor below minimum sample is not presented as a qualifying ranking",
        "No qualifying vendor-level" in low_sample_result.get("vendor_meaning", "")
    ))

    failures = 0
    for name, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        failures += int(not passed)

    print("\nLIMITATIONS")
    print("- Text checks do not prove statistical significance or causality.")
    print("- No real-world breach reduction or realized savings are measured.")
    print("- Review any failed check before treating the candidate as improved.")
    print(f"\nRESULT: {failures} edge-case failure(s); "
          f"vendor score {vendor_score}/{len(VENDOR_RULES)}.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
