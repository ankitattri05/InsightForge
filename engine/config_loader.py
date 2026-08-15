"""
Loads and validates InsightForge semantic configuration files.

Confirms a config is internally consistent BEFORE the analytics engine
ever touches a database. Does not connect to MySQL, run SQL, or check
whether a business number is correct.
"""

from pathlib import Path
import yaml

VALID_KPI_TYPES = {"count", "sum", "average", "rate","calculated"}

REQUIRED_TOP_LEVEL = [
    "project",
    "dataset",
    "database",
    "dimensions",
    "measures",
    "kpis"
]

REQUIRED_DATASET_FIELDS = [
    "grain_column",
    "date_column"
]

REQUIRED_DATABASE_FIELDS = [
    "view"
]


def load_config(config_path: str) -> dict:
    """
    Load a YAML configuration file and validate its structure.
    """

    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    print(path.resolve())
    print(config["project"]["name"])

    _validate(config)

    return config


def _validate(config: dict) -> None:

    missing = [
        section
        for section in REQUIRED_TOP_LEVEL
        if section not in config
    ]

    if missing:
        raise ValueError(
            f"Missing configuration sections: {missing}"
        )

    missing_dataset = [
        field
        for field in REQUIRED_DATASET_FIELDS
        if field not in config["dataset"]
    ]

    if missing_dataset:
        raise ValueError(
            f"'dataset' section missing required fields: {missing_dataset}"
        )

    missing_database = [
        field
        for field in REQUIRED_DATABASE_FIELDS
        if field not in config["database"]
    ]

    if missing_database:
        raise ValueError(
            f"'database' section missing required fields: {missing_database}"
        )

    if not isinstance(config["dimensions"], list) or not config["dimensions"]:
        raise ValueError(
            "'dimensions' must be a non-empty list"
        )

    if not isinstance(config["measures"], list) or not config["measures"]:
        raise ValueError(
            "'measures' must be a non-empty list"
        )

    known_columns = set(config["measures"]) | set(config.get("flags", []))

    for metric_name, metric in config["kpis"].items():

        metric_type = metric.get("type")

        if metric_type not in VALID_KPI_TYPES:
            raise ValueError(
                f"KPI '{metric_name}' has missing or invalid type: "
                f"{metric_type!r}. "
                f"Must be one of {sorted(VALID_KPI_TYPES)}"
            )

        if metric_type not in {"count", "calculated"}:

            column = metric.get("column")

            if not column:
                raise ValueError(
                    f"KPI '{metric_name}' of type "
                    f"'{metric_type}' requires a 'column'"
                )

            if column not in known_columns:
                raise ValueError(
                    f"KPI '{metric_name}' references column "
                    f"'{column}', which is not declared in "
                    f"'measures' or 'flags'"
                )