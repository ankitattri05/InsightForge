"""
Deterministic two-factor business bridge.

Decomposes a change in a business value into:
    volume effect + rate/unit-value effect

This module performs arithmetic only.

No SQL.
No LLM.
No business narrative.
No causal claims.
"""

from math import isclose


def two_factor_bridge(
    previous_volume: float,
    current_volume: float,
    previous_rate: float,
    current_rate: float,
) -> dict:
    """
    Decompose the change in value between two periods.

    Business value is defined as:

        value = volume × rate

    The bridge uses the standard midpoint decomposition:

        volume_effect =
            (current_volume - previous_volume)
            × ((previous_rate + current_rate) / 2)

        rate_effect =
            (current_rate - previous_rate)
            × ((previous_volume + current_volume) / 2)

    Therefore:

        volume_effect + rate_effect
        = current_value - previous_value

    This is a mathematical decomposition, not a causal explanation.

    Raises
    ------
    ValueError
        If any input is non-finite or if the implied previous/current
        values cannot be represented safely.
    """

    values = {
        "previous_volume": previous_volume,
        "current_volume": current_volume,
        "previous_rate": previous_rate,
        "current_rate": current_rate,
    }

    for name, value in values.items():
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"{name} must be numeric."
            )

        if not float("-inf") < float(value) < float("inf"):
            raise ValueError(
                f"{name} must be finite."
            )

    previous_volume = float(previous_volume)
    current_volume = float(current_volume)
    previous_rate = float(previous_rate)
    current_rate = float(current_rate)

    previous_value = (
        previous_volume * previous_rate
    )

    current_value = (
        current_volume * current_rate
    )

    absolute_change = (
        current_value - previous_value
    )

    volume_effect = (
        (current_volume - previous_volume)
        * ((previous_rate + current_rate) / 2)
    )

    rate_effect = (
        (current_rate - previous_rate)
        * ((previous_volume + current_volume) / 2)
    )

    reconstructed_change = (
        volume_effect + rate_effect
    )

    reconciles = isclose(
        reconstructed_change,
        absolute_change,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    if not reconciles:
        raise ValueError(
            "Two-factor bridge failed reconciliation."
        )

    return {
        "previous_volume": previous_volume,
        "current_volume": current_volume,
        "previous_rate": previous_rate,
        "current_rate": current_rate,
        "previous_value": previous_value,
        "current_value": current_value,
        "absolute_change": absolute_change,
        "volume_effect": volume_effect,
        "rate_effect": rate_effect,
        "reconstructed_change": reconstructed_change,
        "reconciles": reconciles,
    }

def bridge_from_periods(
    previous_volume: float,
    current_volume: float,
    previous_rate: float,
    current_rate: float,
) -> dict:
    """
    Build a two-factor bridge for a business value defined as:

        value = volume × rate

    This is a convenience wrapper around two_factor_bridge().
    It adds deterministic labels describing the decomposition.

    The result describes mathematical contribution only.
    It does not establish business causality.
    """

    result = two_factor_bridge(
        previous_volume=previous_volume,
        current_volume=current_volume,
        previous_rate=previous_rate,
        current_rate=current_rate,
    )

    result.update(
        {
            "volume_component": "incident_count",
            "rate_component": "cost_per_incident",
            "value_metric": "total_cost",
            "interpretation_boundary": (
                "Mathematical decomposition of total-cost change; "
                "does not establish business causality."
            ),
        }
    )

    return result