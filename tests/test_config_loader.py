import pytest

from engine.config_loader import load_config


def test_valid_config_loads():
    config = load_config("config/telecom.yaml")
    assert config["project"]["name"] == "Telecom Service Assurance"


def test_missing_section_raises(tmp_path):
    bad = tmp_path / "bad.yaml"

    bad.write_text(
        """
project:
  name: Test
"""
    )

    with pytest.raises(ValueError, match="Missing configuration sections"):
        load_config(str(bad))


def test_kpi_column_not_declared_raises(tmp_path):
    bad = tmp_path / "bad.yaml"

    bad.write_text(
        """
project:
  name: Test

dataset:
  grain_column: id
  date_column: dt

database:
  view: v

dimensions:
  - state

measures:
  - cost

kpis:
  total_cost:
    type: sum
    column: unknown_column
"""
    )

    with pytest.raises(ValueError, match="not declared"):
        load_config(str(bad))