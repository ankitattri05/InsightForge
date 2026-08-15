# Business Interpretation Matrix

## Purpose

The Business Interpretation Matrix defines how every Key Performance Indicator (KPI)
is transformed into a deterministic business finding before it reaches the LLM.

InsightForge follows a strict separation of responsibilities:

Database
→ stores business data

SQL
→ retrieves and aggregates data

Python Analytics Engine
→ calculates KPIs

Business Interpretation Layer
→ converts KPIs into business findings

LLM Narrator
→ communicates verified findings in executive language

The narrator never determines whether a KPI is good, bad, normal,
or critical. That responsibility belongs exclusively to the deterministic
analytics engine.

---

# Architectural Principle

Every KPI exposed to the narrator must already contain its business meaning.

The LLM must never decide:

- whether performance is acceptable
- whether a KPI is improving
- whether operational risk exists
- whether management attention is required

Those conclusions are deterministic business logic implemented in Python.

---

# KPI Interpretation Categories

Not every KPI should be interpreted in the same way.

InsightForge classifies KPIs into three categories.

---

## 1. Benchmark KPIs

Definition

A Benchmark KPI has a legitimate business target or contractual threshold.

Interpretation is performed by comparing the KPI against that benchmark.

Examples

- SLA Breach Rate
- Future contractual SLA metrics

Example Finding

Status: Warning

Business Finding:

SLA breach rate exceeds the preferred operating target and requires management attention.

---

## 2. Baseline KPIs

Definition

A Baseline KPI cannot be interpreted from its absolute value alone.

It must be compared against historical performance or another valid baseline.

Examples

- Incident Count
- Average Resolution Time (future implementation)

Correct Question

Is workload higher than normal?

Incorrect Question

Is 25,000 incidents good?

There is no meaningful answer without a baseline.

Phase 2

Average Resolution Time will temporarily use documented heuristic rules.

Future versions may compare against historical or severity-weighted baselines.

---

## 3. Descriptive KPIs

Definition

Some KPIs describe business composition rather than business quality.

These KPIs should not receive artificial Good / Warning / Critical labels.

Examples

- Dispatch Cost %
- Service Impact Cost %
- Escalation Rate

These metrics provide context rather than judgement.

Example

Dispatch Cost = 34%

This is descriptive information.

Management decides whether this trend is acceptable.

---

# KPI Interpretation Matrix

| KPI | Category | Business Question | Interpretation Method |
|------|----------|------------------|-----------------------|
| Incident Count | Baseline | Is workload abnormal? | Compare against historical baseline (future implementation) |
| SLA Breach Rate | Benchmark | Is customer experience at risk? | Threshold comparison |
| Average Resolution Time | Baseline (future) / Heuristic (Phase 2) | Is support operating efficiently? | Temporary heuristic |
| Total Cost-to-Serve | Derived | Is support financially sustainable? | Never interpret raw total directly |

---

# Derived Business KPIs

Raw totals often have little business meaning without context.

Instead of interpreting Total Cost directly, InsightForge derives more meaningful KPIs.

## Cost per Incident

Business Question

Is operational efficiency improving?

Interpretation

Trend comparison.

Never a fixed threshold.

---

## Dispatch Cost %

Business Question

How dependent is service restoration on field dispatch?

Interpretation

Descriptive ratio.

---

## Service Impact Cost %

Business Question

What proportion of total cost is driven by customer impact rather than operational effort?

Interpretation

Descriptive ratio.

---

## Escalation Rate

Business Question

Are incidents escalating beyond normal operational handling?

Interpretation

Descriptive rate.

May later be cross-referenced with SLA Breach Rate.

---

# Business Rule Design Principles

Every business interpretation implemented in InsightForge must satisfy all of the following.

## Rule 1

Every KPI must answer a real business question.

---

## Rule 2

Every business interpretation must be deterministic.

The same input must always produce the same finding.

---

## Rule 3

Raw totals must never receive arbitrary thresholds.

Every threshold must have a legitimate business justification.

---

## Rule 4

If a KPI cannot be interpreted legitimately,
derive a better KPI instead of inventing business rules.

---

## Rule 5

Business logic belongs in Python.

Narrative belongs in the LLM.

---

## Rule 6

Every interpretation must improve decision-making.

A KPI exists only if it helps management make a better operational decision.

---

## Rule 7

Every interpretation must increase hiring value.

If a KPI or business rule does not demonstrate analytical thinking expected from a Business Analyst, Data Analyst, or BI Analyst, it should not be implemented.

---

# Relationship to Other Components

This document defines the business contract for:

config/telecom.yaml
→ threshold configuration

engine/findings.py
→ deterministic interpretation engine

agent/tools.py
→ exposes verified findings

agent/narrator.py
→ executive communication only

Changes to business interpretation should begin in this document before implementation.