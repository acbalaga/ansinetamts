from typing import Dict, List

import streamlit_app


def test_summary_prefers_error_when_failures_present() -> None:
    measurements = [1.0, 2.0, 3.0]
    statuses = ["Pass", "Fail", "Fail"]
    details = ["ok", "too high", "still high"]
    criterion: Dict[str, object] = {"note": "Use caution on re-energization."}

    severity, summary = streamlit_app.summarize_series_outcome(
        measurements, statuses, details, criterion
    )

    assert severity == "error"
    assert "2 measurement(s) exceeded" in summary
    assert "Latest status: Fail" in summary
    assert "Trend appears increasing" in summary
    assert criterion["note"] in summary


def test_summary_highlights_investigate_when_only_cautions_present() -> None:
    measurements = [5.0, 4.1, 3.2]
    statuses = ["Pass", "Investigate", "Investigate"]
    details = ["steady", "dipping", "closer to limit"]
    criterion: Dict[str, object] = {}

    severity, summary = streamlit_app.summarize_series_outcome(
        measurements, statuses, details, criterion
    )

    assert severity == "warning"
    assert "2 measurement(s) entered the investigate band" in summary
    assert "Latest status: Investigate" in summary
    assert "Trend appears decreasing" in summary


def test_summary_marks_success_when_all_within_band() -> None:
    measurements = [2.0, 2.0, 2.0]
    statuses = ["Pass", "Pass", "Pass"]
    details = ["stable"] * 3
    criterion: Dict[str, object] = {}

    severity, summary = streamlit_app.summarize_series_outcome(
        measurements, statuses, details, criterion
    )

    assert severity == "success"
    assert "All 3 readings remain within the advisory band" in summary
    assert "Trend appears flat" in summary
