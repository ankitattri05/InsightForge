# Project Structure

```
InsightForge/
│
├── agent/
├── config/
├── docs/
├── engine/
├── sql/
├── .env
├── main.py
├── requirements.txt
└── README.md
```

## Directory Responsibilities

| Directory / File | Responsibility |
|------------------|----------------|
| `agent/` | Executive narration layer, prompts, tool definitions, and report generation. |
| `engine/` | Deterministic KPI calculations, business interpretation, diagnostics, database access, and analytical logic. |
| `config/` | YAML configuration files containing project metadata, KPI definitions, thresholds, and database settings. |
| `sql/` | SQL scripts for schema creation, analytical views, and supporting queries. |
| `docs/` | Technical documentation including architecture, project structure, business requirements, and data dictionary. |
| `main.py` | Application entry point that generates the executive report and launches the interactive analyst. |
| `requirements.txt` | Python package dependencies required to run the project. |
| `.env` | Environment variables including database and API credentials (not committed to GitHub). |
| `README.md` | Project overview, installation guide, and usage instructions. |


## Design Philosophy

The repository follows a modular architecture where each component has a single responsibility.

- **SQL** is responsible for data aggregation.
- **Python** is responsible for deterministic KPI computation and business interpretation.
- **Configuration** controls project-specific behavior through YAML files.
- **The Executive Narration Layer** communicates verified findings without performing analytical calculations.

This separation improves maintainability, simplifies testing, and ensures every reported business finding remains traceable to deterministic analytics.