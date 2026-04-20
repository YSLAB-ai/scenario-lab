from forecasting_harness.compatibility import compare_state_slices


def test_compatibility_uses_normalized_values_not_display_text() -> None:
    previous = {
        "morale": {"normalized_value": 0.8},
        "fuel_days": {"normalized_value": 12},
    }
    current = {
        "morale": {"normalized_value": 0.9},
        "fuel_days": {"normalized_value": 12},
    }

    result = compare_state_slices(
        previous,
        current,
        tolerances={"morale": 0.2, "fuel_days": 0.0},
    )

    assert result["compatible"] is True
    assert result["changed_fields"] == ["morale"]
