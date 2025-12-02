import math
from typing import Dict

import streamlit_app


def test_absolute_thresholds_cover_fail_and_pass_cases() -> None:
    criterion: Dict[str, object] = {
        "evaluation_type": "absolute",
        "parameter": "resistance",
        "unit": "MΩ",
        "minimum": 5.0,
        "maximum": 10.0,
    }

    low_result = streamlit_app.evaluate_measurement(4.5, criterion)
    assert low_result["status"] == "Fail"
    assert "below minimum of 5.0" in low_result["detail"]

    mid_result = streamlit_app.evaluate_measurement(7.5, criterion)
    assert mid_result["status"] == "Pass"
    assert "Measured value: 7.50" in mid_result["detail"]

    high_result = streamlit_app.evaluate_measurement(11.2, criterion)
    assert high_result["status"] == "Fail"
    assert "above maximum of 10.0" in high_result["detail"]


def test_investigate_thresholds_apply_before_hard_limits() -> None:
    criterion: Dict[str, object] = {
        "evaluation_type": "absolute",
        "parameter": "voltage",
        "unit": "kV",
        "investigate_below": 12.0,
        "investigate_above": 24.0,
        "maximum": 30.0,
    }

    below_caution = streamlit_app.evaluate_measurement(10.0, criterion)
    assert below_caution["status"] == "Investigate"
    assert "below caution threshold of 12.0" in below_caution["detail"]

    above_caution = streamlit_app.evaluate_measurement(26.0, criterion)
    assert above_caution["status"] == "Investigate"
    assert "above caution threshold of 24.0" in above_caution["detail"]

    above_max = streamlit_app.evaluate_measurement(31.0, criterion)
    assert above_max["status"] == "Fail"
    assert "above maximum of 30.0" in above_max["detail"]


def test_percentage_change_requires_baseline_and_computes_when_present() -> None:
    criterion: Dict[str, object] = {
        "evaluation_type": "percentage_change",
        "parameter": "current",
        "unit": "A",
        "maximum": 25.0,
    }

    missing_baseline = streamlit_app.evaluate_measurement(120.0, criterion, baseline=None)
    assert missing_baseline["status"] == "Info"
    assert "Baseline or reference value is required" in missing_baseline["detail"]

    with_baseline = streamlit_app.evaluate_measurement(125.0, criterion, baseline=100.0)
    assert math.isclose(float(with_baseline["detail"].split()[2].rstrip('%')), 25.0)
    assert with_baseline["status"] == "Pass"


def test_qualitative_criteria_always_request_review() -> None:
    criterion: Dict[str, object] = {
        "evaluation_type": "qualitative",
        "parameter": "observation",
        "label": "Visual assessment",
    }

    result = streamlit_app.evaluate_measurement(0.0, criterion)
    assert result["status"] == "Review"
    assert "qualitative checks rely on professional judgment" in result["detail"]
