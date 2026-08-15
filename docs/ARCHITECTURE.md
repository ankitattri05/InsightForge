# InsightForge Architecture

## 1. Overview

InsightForge is a modular Business Intelligence framework designed to produce deterministic executive analytics from structured business data.

The platform separates data processing, analytical computation, business interpretation, and executive narration into independent layers. SQL is responsible for data aggregation, Python performs KPI computation and applies deterministic business rules, and the language model is restricted to communicating verified findings. This separation ensures analytical results remain explainable, reproducible, and traceable to deterministic calculations.

## 2. Design Principles

- Deterministic analytics over AI-generated calculations.
- SQL-first architecture for all business aggregations.
- Configuration-driven metric definitions.
- Explainable business interpretations.
- Strict separation between analytics and narration.
- Evidence-first reporting with no unsupported inference.

## 3. System Architecture

```text
Raw Data
    │
    ▼
SQL Analytics
    │
    ▼
Deterministic KPI Engine (Python)
    │
    ▼
Business Interpretation Layer (Python)
    │
    ▼
Executive Narration Layer (Claude)
    │
    ▼
Executive Report / Interactive Analyst
```

## 4. Layer Responsibilities

### 4.1 SQL Analytics Layer

- Performs all aggregations and business calculations at the database level.
- Returns deterministic values only.
- Never generates business interpretations.

### 4.2 Deterministic KPI Engine

- Retrieves verified metrics from SQL.
- Computes KPI values.
- Formats metrics for reporting.
- Acts as the single source of truth for all reported values.

### 4.3 Business Interpretation Layer

- Applies deterministic business rules.
- Generates verified interpretations, diagnostics, and classifications.
- Never uses AI for analytical reasoning.

### 4.4 Executive Narration Layer

- Converts verified findings into executive language.
- Improves readability and report structure.
- Never calculates metrics or invents business conclusions.

## 5. Deterministic AI Boundary

The language model is intentionally isolated from the analytical workflow.

All calculations, KPI evaluation, business rules, classifications, and diagnostic rankings are produced by deterministic Python modules. The language model receives only these verified outputs and is limited to presenting them in clear business language.

It cannot calculate metrics, derive new findings, establish causal relationships, or strengthen analytical evidence beyond what has already been produced by the analytics engine.

## 6. Analytics Workflow

The reporting workflow follows a fixed execution sequence:

1. Load project configuration from the YAML configuration file.
2. Execute deterministic SQL queries against the configured analytical view.
3. Calculate requested business metrics using the KPI engine.
4. Apply deterministic interpretation rules and diagnostic analysis.
5. Format verified findings for presentation.
6. Pass verified findings to the executive narration layer.
7. Generate either an executive report or an interactive analytical response.

## 7. Configuration-Driven Design

Business behaviour is controlled through external configuration rather than application code.

Each project defines its own database settings, KPI catalogue, business thresholds, reporting metadata, and dataset properties within a YAML configuration file. The analytics engine consumes this configuration at runtime, allowing the same framework to support different business domains without modifying core analytical logic.

## 8. Project Structure Responsibilities

| Directory | Responsibility |
|-----------|----------------|
| `agent/` | Executive narration layer, prompts, and tool orchestration |
| `engine/` | Deterministic KPI calculations, business interpretation, diagnostics, and database access |
| `config/` | Project configuration, KPI definitions, thresholds, and metadata |
| `sql/` | SQL scripts for schema creation, views, and analytical queries |
| `docs/` | Project documentation |
| `main.py` | Application entry point and interactive CLI |

## 9. Design Decisions

- SQL performs all business aggregations.
- Python is responsible for deterministic KPI computation and business interpretation.
- The LLM never performs analytical calculations.
- Every reported finding is traceable to deterministic analytics.
- Configuration-driven design minimizes code changes when supporting new business domains.
- The architecture prioritizes explainability, maintainability, and business transparency over unnecessary complexity.

## 10. Future Enhancements

Potential future enhancements include:

- Historical period-over-period comparisons
- Additional deterministic KPI libraries
- Domain-specific analytics modules
- Interactive dashboard integration
- Expanded diagnostic coverage
- Multi-domain configuration support