import pytest

from engine.bridge import two_factor_bridge


def test_two_factor_bridge_reconciles():

    result = two_factor_bridge(
        previous_volume=100,
        current_volume=120,
        previous_rate=10,
        current_rate=12,
    )

    assert result["previous_value"] == 1000
    assert result["current_value"] == 1440
    assert result["absolute_change"] == 440

    assert result["volume_effect"] == 220
    assert result["rate_effect"] == 220

    assert result["reconciles"] is True


def test_volume_only_change():

    result = two_factor_bridge(
        previous_volume=100,
        current_volume=120,
        previous_rate=10,
        current_rate=10,
    )

    assert result["absolute_change"] == 200
    assert result["volume_effect"] == 200
    assert result["rate_effect"] == 0
    assert result["reconciles"] is True


def test_rate_only_change():

    result = two_factor_bridge(
        previous_volume=100,
        current_volume=100,
        previous_rate=10,
        current_rate=12,
    )

    assert result["absolute_change"] == 200
    assert result["volume_effect"] == 0
    assert result["rate_effect"] == 200
    assert result["reconciles"] is True


def test_decrease_reconciles():

    result = two_factor_bridge(
        previous_volume=120,
        current_volume=100,
        previous_rate=12,
        current_rate=10,
    )

    assert result["absolute_change"] == -440
    assert result["reconciles"] is True


def test_zero_volume_is_valid():

    result = two_factor_bridge(
        previous_volume=0,
        current_volume=100,
        previous_rate=10,
        current_rate=10,
    )

    assert result["previous_value"] == 0
    assert result["current_value"] == 1000
    assert result["absolute_change"] == 1000
    assert result["reconciles"] is True


def test_non_numeric_input_rejected():

    with pytest.raises(ValueError):
        two_factor_bridge(
            previous_volume="100",
            current_volume=120,
            previous_rate=10,
            current_rate=12,
        )


def test_non_finite_input_rejected():

    with pytest.raises(ValueError):
        two_factor_bridge(
            previous_volume=float("inf"),
            current_volume=120,
            previous_rate=10,
            current_rate=12,
        )

def test_bridge_from_periods_preserves_reconciliation():

    from engine.bridge import bridge_from_periods

    result = bridge_from_periods(
        previous_volume=100,
        current_volume=120,
        previous_rate=10,
        current_rate=12,
    )

    assert result["value_metric"] == "total_cost"
    assert result["volume_component"] == "incident_count"
    assert result["rate_component"] == "cost_per_incident"
    assert result["previous_value"] == 1000
    assert result["current_value"] == 1440
    assert result["absolute_change"] == 440
    assert result["reconciles"] is True


def test_bridge_from_periods_does_not_claim_causality():

    from engine.bridge import bridge_from_periods

    result = bridge_from_periods(
        previous_volume=100,
        current_volume=110,
        previous_rate=10,
        current_rate=11,
    )

    assert "causality" in result["interpretation_boundary"]