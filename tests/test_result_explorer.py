from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit_app


@dataclass
class StubStreamlit:
    data_mode: str = "Manual entry"
    raw_values: str = ""
    baseline_value: float = 100.0
    selected_option: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    successes: List[str] = field(default_factory=list)
    infos: List[str] = field(default_factory=list)
    captions: List[str] = field(default_factory=list)
    dataframe_data: Optional[pd.DataFrame] = None
    session_state: Dict[str, Any] = field(default_factory=dict)

    def subheader(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def selectbox(self, _label: str, options: List[str], format_func=None, **_kwargs: Any) -> str:
        return self.selected_option or options[0]

    def radio(self, *_args: Any, **_kwargs: Any) -> str:
        return self.data_mode

    def text_area(self, *_args: Any, **_kwargs: Any) -> str:
        return self.raw_values

    def number_input(self, *_args: Any, **_kwargs: Any) -> float:
        return self.baseline_value

    def select_slider(self, *_args: Any, **_kwargs: Any) -> str:
        return "Healthy"

    def slider(self, *_args: Any, **_kwargs: Any) -> int:
        return 4

    def warning(self, message: str, **_kwargs: Any) -> None:
        self.warnings.append(message)

    def error(self, message: str, **_kwargs: Any) -> None:
        self.errors.append(message)

    def success(self, message: str, **_kwargs: Any) -> None:
        self.successes.append(message)

    def info(self, message: str, **_kwargs: Any) -> None:
        self.infos.append(message)

    def caption(self, message: str, **_kwargs: Any) -> None:
        self.captions.append(message)

    def code(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def metric(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def button(self, *_args: Any, **_kwargs: Any) -> bool:
        return False

    def dataframe(self, data: pd.DataFrame, **_kwargs: Any) -> None:
        self.dataframe_data = data

    def line_chart(self, *_args: Any, **_kwargs: Any) -> None:
        return None


    def __getattr__(self, _name: str) -> Any:  # pragma: no cover
        # Provide no-op fallbacks for any Streamlit functions not explicitly stubbed.
        return lambda *args, **kwargs: None


def build_index() -> Dict[str, Dict[str, Dict[str, Any]]]:
    criterion: Dict[str, Any] = {
        "id": "criterion-1",
        "label": "Test criterion",
        "parameter": "resistance",
        "unit": "Ω",
        "evaluation_type": "absolute",
        "maximum": 2.5,
        "investigate_above": 2.0,
    }
    test: Dict[str, Any] = {
        "id": "sample",
        "name": "Sample test",
        "criteria": [criterion],
        "result_implications": {},
    }
    return {criterion["id"]: {"test": test, "criterion": criterion}}


def test_explorer_shows_guard_message_when_no_measurements(monkeypatch) -> None:
    index = build_index()
    stub = StubStreamlit(raw_values="")
    monkeypatch.setattr(streamlit_app, "st", stub)

    streamlit_app.render_result_explorer(index)

    assert any("Provide at least one numeric value" in message for message in stub.warnings)


def test_explorer_assessment_matches_measurements(monkeypatch) -> None:
    index = build_index()
    stub = StubStreamlit(raw_values="1, 2.1, 2.6")
    monkeypatch.setattr(streamlit_app, "st", stub)

    streamlit_app.render_result_explorer(index)

    assert stub.dataframe_data is not None
    assert stub.dataframe_data["Assessment"].tolist() == ["Pass", "Investigate", "Fail"]
    assert len(stub.errors) == 1
