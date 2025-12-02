"""Streamlit learning lab for ANSI/NETA MTS 2023."""
from __future__ import annotations

import json
from collections import Counter
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

DEFAULT_TEST_DATA_PATH = Path(__file__).resolve().parent / "data" / "tests.json"

st.set_page_config(
    page_title="ANSI-NETA MTS 2023 Learning Lab",
    layout="wide",
    page_icon="⚡",
)


@dataclass
class TestDefinition:
    """Validate the shape of a single test entry."""

    payload: Dict[str, Any]

    REQUIRED_FIELDS = {
        "id",
        "name",
        "category",
        "summary",
        "equipment",
        "phases",
        "purpose",
        "procedure",
        "interpretation",
        "criteria",
        "diagnostics",
        "result_implications",
        "deep_dive",
    }
    STRING_FIELDS = {"id", "name", "category", "summary", "purpose", "interpretation"}
    LIST_FIELDS = {"equipment", "phases", "procedure", "criteria"}

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TestDefinition":
        if not isinstance(payload, dict):
            raise ValueError("Each test entry must be a mapping of fields.")

        cls._validate_required_fields(payload)
        cls._validate_criteria(payload["criteria"])
        cls._validate_deep_dive(payload["deep_dive"])
        return cls(payload=payload)

    @property
    def id(self) -> str:
        return str(self.payload["id"])

    def to_dict(self) -> Dict[str, Any]:
        return self.payload

    @classmethod
    def _validate_required_fields(cls, payload: Dict[str, Any]) -> None:
        missing = cls.REQUIRED_FIELDS - payload.keys()
        if missing:
            raise ValueError(f"Missing required test fields: {', '.join(sorted(missing))}")

        for field in cls.STRING_FIELDS:
            if not isinstance(payload[field], str) or not payload[field].strip():
                raise ValueError(f"Field '{field}' must be a non-empty string.")

        for field in cls.LIST_FIELDS:
            if not isinstance(payload[field], list):
                raise ValueError(f"Field '{field}' must be a list.")

        if not isinstance(payload.get("diagnostics"), dict):
            raise ValueError("Field 'diagnostics' must be a mapping.")
        if not isinstance(payload.get("result_implications"), dict):
            raise ValueError("Field 'result_implications' must be a mapping.")
        if not isinstance(payload.get("deep_dive"), dict):
            raise ValueError("Field 'deep_dive' must be a mapping.")

    @classmethod
    def _validate_criteria(cls, criteria: List[Dict[str, Any]]) -> None:
        if not criteria:
            raise ValueError("At least one criterion is required for each test.")

        required_fields = {"id", "label", "parameter", "unit", "evaluation_type"}
        numeric_fields = {"minimum", "maximum", "investigate_below", "investigate_above"}

        for criterion in criteria:
            if not isinstance(criterion, dict):
                raise ValueError("Each criterion must be a mapping.")

            missing = required_fields - criterion.keys()
            if missing:
                raise ValueError(f"Criterion missing fields: {', '.join(sorted(missing))}")

            for field in required_fields:
                if not isinstance(criterion[field], str) or not criterion[field]:
                    raise ValueError(f"Criterion field '{field}' must be a non-empty string.")

            for field in numeric_fields:
                if field in criterion and not isinstance(criterion[field], (int, float)):
                    raise ValueError(
                        f"Criterion field '{field}' must be numeric when provided."
                    )

    @classmethod
    def _validate_deep_dive(cls, deep_dive: Dict[str, Any]) -> None:
        required_fields = {"title", "summary", "sections"}
        missing = required_fields - deep_dive.keys()
        if missing:
            raise ValueError(f"Deep dive missing fields: {', '.join(sorted(missing))}")

        if not isinstance(deep_dive["title"], str) or not isinstance(
            deep_dive["summary"], str
        ):
            raise ValueError("Deep dive title and summary must be strings.")

        sections = deep_dive["sections"]
        if not isinstance(sections, list) or not sections:
            raise ValueError("Deep dive sections must be a non-empty list.")

        for section in sections:
            if not isinstance(section, dict):
                raise ValueError("Each deep dive section must be a mapping.")
            if "title" not in section or "bullets" not in section:
                raise ValueError("Each deep dive section requires a title and bullets.")
            if not isinstance(section["title"], str):
                raise ValueError("Deep dive section titles must be strings.")
            if not isinstance(section["bullets"], list):
                raise ValueError("Deep dive section bullets must be a list of strings.")
            for bullet in section["bullets"]:
                if not isinstance(bullet, str):
                    raise ValueError("Deep dive bullets must be strings.")


def load_test_library(path: str | Path = DEFAULT_TEST_DATA_PATH) -> List[Dict[str, Any]]:
    """Load and validate test definitions from structured data files.

    The loader keeps the UI decoupled from the source data. Provide a JSON file
    that matches the expected structure. YAML is also supported if converted
    before parsing.

    Example:
        tests = load_test_library()
    """

    data_path = Path(path)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Test library file not found at {data_path}. Ensure data/tests.json is present."
        )

    try:
        raw_data = json.loads(data_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse test library data: {exc}") from exc

    if not isinstance(raw_data, list):
        raise ValueError("Test library root must be a list of test definitions.")

    tests: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for entry in raw_data:
        definition = TestDefinition.from_dict(entry)
        if definition.id in seen_ids:
            raise ValueError(f"Duplicate test id found: {definition.id}")
        seen_ids.add(definition.id)
        tests.append(definition.to_dict())

    return tests


def _stable_seed(*parts: str) -> int:
    seed = 0
    for part in parts:
        for char in str(part):
            seed = (seed * 31 + ord(char)) % 2**32
    return seed or 1


def _suggest_seed_values(criterion: Dict) -> List[float]:
    values, _ = simulate_measurements(criterion, scenario="Healthy", count=3)
    return values


IR_DEFAULT_RATING_KV = 34.5


def recommend_dc_test_voltage(
    nameplate_kv: float, table: List[Dict[str, float]]
) -> float:
    """Return the suggested megohmmeter voltage based on ANSI/NETA-style tables."""
    if not table:
        return 0.0
    for row in table:
        if nameplate_kv <= row["max_rating_kv"]:
            return row["dc_test_kv"]
    return table[-1]["dc_test_kv"]


def describe_test_voltage_application(
    applied_kv: float, recommended_kv: float
) -> Tuple[str, str]:
    """Return (severity, message) describing adequacy of applied DC voltage."""
    if recommended_kv <= 0:
        return "info", "Enter a nameplate voltage to receive test-stress guidance."

    if applied_kv < 0.85 * recommended_kv:
        return (
            "warning",
            "Applied DC voltage is significantly below the typical ANSI/NETA recommendation — megohm readings may appear artificially high.",
        )
    if applied_kv > 1.2 * recommended_kv:
        return (
            "warning",
            "Applied DC voltage exceeds the usual stress level. Confirm the insulation system is rated for this voltage to avoid overstressing aged assets.",
        )
    return (
        "info",
        "Test voltage aligns with ANSI/NETA guidance, so resistance values represent a valid stress level.",
    )


def describe_result_meaning(status: str, test: Dict) -> Optional[str]:
    mapping = test.get("result_implications") or {}
    return mapping.get(status) or mapping.get("default")


def render_deep_dive_section(test: Dict) -> None:
    deep_dive = test.get("deep_dive")
    if not deep_dive:
        return

    title = deep_dive.get("title") or f"{test['name']} deep dive"
    with st.expander(f"Deep dive — {title}"):
        summary = deep_dive.get("summary")
        if summary:
            st.write(summary)

        for section in deep_dive.get("sections", []):
            heading = section.get("title")
            if heading:
                st.markdown(f"**{heading}**")
            for bullet in section.get("bullets", []):
                st.write(f"- {bullet}")
            text = section.get("text")
            if text:
                st.write(text)

        for table in deep_dive.get("tables", []):
            table_title = table.get("title")
            if table_title:
                st.markdown(f"**{table_title}**")
            df = pd.DataFrame(table.get("rows", []))
            columns = table.get("columns")
            if columns:
                df = df[[col for col in columns if col in df.columns]]
            st.table(df)
            caption = table.get("caption")
            if caption:
                st.caption(caption)

        for callout in deep_dive.get("callouts", []):
            style = callout.get("style", "info")
            message = callout.get("text")
            renderer = {
                "success": st.success,
                "info": st.info,
                "warning": st.warning,
                "error": st.error,
            }.get(style, st.info)
            if message:
                renderer(message)


def render_voltage_context(test: Dict, widget_suffix: str) -> Optional[Dict[str, float]]:
    table = test.get("kv_recommendations")
    if not table:
        return None

    st.markdown("**Test voltage context**")
    col_rating, col_applied = st.columns(2)
    default_rating = min(IR_DEFAULT_RATING_KV, table[-1]["max_rating_kv"])
    nameplate = col_rating.number_input(
        "Equipment nameplate voltage (kV line-line)",
        min_value=0.1,
        value=float(default_rating),
        step=0.1,
        key=f"rating_{widget_suffix}",
    )
    recommended = recommend_dc_test_voltage(nameplate, table)
    col_rating.caption(f"Suggested ANSI/NETA DC test voltage: {recommended:.1f} kV")

    default_applied = recommended or table[0]["dc_test_kv"]
    applied = col_applied.number_input(
        "Applied DC test voltage (kV)",
        min_value=0.1,
        value=float(default_applied),
        step=0.1,
        key=f"applied_{widget_suffix}",
    )

    severity, message = describe_test_voltage_application(applied, recommended)
    renderer = {"warning": st.warning, "info": st.info}.get(severity, st.info)
    renderer(message)

    return {
        "nameplate_kv": nameplate,
        "recommended_kv": recommended,
        "applied_kv": applied,
    }


def simulate_measurements(
    criterion: Dict, scenario: str = "Drifting", count: int = 6
) -> Tuple[List[float], Optional[float]]:
    rng = random.Random(_stable_seed(criterion["id"], scenario, count))
    eval_type = criterion.get("evaluation_type", "absolute")
    baseline: Optional[float] = None

    if eval_type == "percentage_change":
        baseline = 100.0
        limit_pct = (
            criterion.get("maximum")
            or criterion.get("investigate_above")
            or criterion.get("investigate_below")
            or 10.0
        )
        start_pct = {
            "Healthy": limit_pct * 0.25,
            "Drifting": limit_pct * 0.65,
            "Out of tolerance": limit_pct * 0.95,
        }[scenario]
        end_pct = {
            "Healthy": limit_pct * 0.45,
            "Drifting": limit_pct * 0.95,
            "Out of tolerance": limit_pct * 1.3,
        }[scenario]
        values: List[float] = []
        span = max(count - 1, 1)
        for idx in range(count):
            pct = start_pct + (end_pct - start_pct) * (idx / span)
            pct += rng.uniform(-0.05, 0.05) * limit_pct
            pct = max(pct, 0)
            values.append(baseline * (1 + pct / 100))
        return values, baseline

    limit_max = criterion.get("maximum")
    limit_min = criterion.get("minimum")
    span = max(count - 1, 1)

    if limit_max is not None:
        start_factor = {
            "Healthy": 0.55,
            "Drifting": 0.75,
            "Out of tolerance": 0.9,
        }[scenario]
        end_factor = {
            "Healthy": 0.7,
            "Drifting": 0.98,
            "Out of tolerance": 1.2,
        }[scenario]
        start = limit_max * start_factor
        end = limit_max * end_factor
    elif limit_min is not None:
        start_factor = {
            "Healthy": 1.35,
            "Drifting": 1.2,
            "Out of tolerance": 1.05,
        }[scenario]
        end_factor = {
            "Healthy": 1.25,
            "Drifting": 0.95,
            "Out of tolerance": 0.75,
        }[scenario]
        start = limit_min * start_factor
        end = limit_min * end_factor
    else:
        start = 1.0 if scenario == "Healthy" else 1.2
        end = 1.05 if scenario == "Healthy" else 1.35

    values = []
    for idx in range(count):
        blend = idx / span
        target = start + (end - start) * blend
        jitter_basis = limit_max or limit_min or target or 1.0
        jitter = rng.uniform(-0.05, 0.05) * jitter_basis
        values.append(round(max(target + jitter, 0.0001), 4))

    return values, baseline


def parse_measurement_series(raw_values: str) -> Tuple[List[float], List[str]]:
    tokens = re.split(r"[\s,;\-/,]+", raw_values.strip()) if raw_values else []
    values: List[float] = []
    invalid: List[str] = []
    for token in tokens:
        chunk = token.strip().strip(",")
        if not chunk:
            continue
        try:
            values.append(float(chunk))
        except ValueError:
            invalid.append(chunk)
    return values, invalid


def format_series(values: List[float]) -> str:
    return ", ".join(f"{value:.3f}" for value in values)


def summarize_series_outcome(
    measurements: List[float],
    statuses: List[str],
    details: List[str],
    criterion: Dict,
) -> Tuple[str, str]:
    counts = Counter(statuses)
    latest_detail = details[-1]
    latest_status = statuses[-1]
    first = measurements[0]
    last = measurements[-1]
    if last > first + 1e-9:
        trend = "increasing"
    elif last < first - 1e-9:
        trend = "decreasing"
    else:
        trend = "flat"

    note = criterion.get("note")

    if counts.get("Fail"):
        severity = "error"
        summary = (
            f"{counts['Fail']} measurement(s) exceeded the published limit. "
            f"Latest status: {latest_status} — {latest_detail}."
        )
    elif counts.get("Investigate"):
        severity = "warning"
        summary = (
            f"{counts['Investigate']} measurement(s) entered the investigate band. "
            f"Latest status: {latest_status} — {latest_detail}."
        )
    else:
        severity = "success"
        summary = (
            f"All {len(measurements)} readings remain within the advisory band. "
            f"Latest detail: {latest_detail}."
        )

    summary += f" Trend appears {trend}."
    if note:
        summary += f" {note}"
    return severity, summary


def build_criteria_index(tests: List[Dict]) -> Dict[str, Dict]:
    index: Dict[str, Dict] = {}
    for test in tests:
        for criterion in test["criteria"]:
            index[criterion["id"]] = {"test": test, "criterion": criterion}
    return index


def is_dga_test(test: Dict) -> bool:
    return test.get("id") == "transformer_dga"


def classify_dga_gas(value: float, gas_meta: Dict) -> Tuple[str, str]:
    if value <= 0:
        return "Not entered", "Provide ppm to compare against the Condition 1–4 guideposts."

    cond2 = gas_meta.get("condition_2")
    cond3 = gas_meta.get("condition_3")
    cond4 = gas_meta.get("condition_4")

    if cond2 is None or cond3 is None or cond4 is None:
        return "Info", "Thresholds unavailable for this gas."

    if value < cond2:
        condition = "Condition 1"
        action = "Normal aging — continue routine annual sampling."
    elif value < cond3:
        condition = "Condition 2"
        action = f"Elevated trend — increase sampling cadence. {gas_meta.get('insight', '')}".strip()
    elif value < cond4:
        condition = "Condition 3"
        action = (
            f"Developing {gas_meta.get('faults', 'faults')} signature — coordinate targeted electrical tests."
        )
    else:
        condition = "Condition 4"
        action = (
            f"Severe {gas_meta.get('faults', 'fault')} indication — prepare for an outage and deeper diagnostics."
        )

    return condition, action


def render_dga_gas_breakdown(test: Dict, widget_suffix: str, context_label: str) -> None:
    gas_meta = test.get("gas_thresholds")
    if not gas_meta:
        return

    st.markdown(f"#### {context_label}: key-gas interpretation")
    st.caption(
        "Enter ppm from your latest oil report to compare with IEEE C57.104-2019 and IEC 60599 guidance."
    )

    cols = st.columns(3)
    gas_values: Dict[str, float] = {}
    for idx, meta in enumerate(gas_meta):
        col = cols[idx % 3]
        gas_values[meta["id"]] = col.number_input(
            f"{meta['gas']} (ppm)",
            min_value=0.0,
            value=0.0,
            key=f"dga_{meta['id']}_{widget_suffix}",
            step=1.0,
        )

    if not any(value > 0 for value in gas_values.values()):
        st.info("Populate at least one gas concentration to see targeted insight.")
        return

    rows = []
    for meta in gas_meta:
        ppm = gas_values.get(meta["id"], 0.0)
        condition, interpretation = classify_dga_gas(ppm, meta)
        rows.append(
            {
                "Gas": meta["gas"],
                "ppm": f"{ppm:.1f}",
                "Condition": condition,
                "What it suggests": interpretation or meta.get("faults", ""),
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.caption(
        "Thresholds paraphrased from IEEE C57.104-2019 and IEC 60599 so readers can trace the original sources."
    )


def evaluate_measurement(
    value: float,
    criterion: Dict,
    baseline: Optional[float] = None,
) -> Dict[str, str]:
    eval_type = criterion.get("evaluation_type", "absolute")
    status = "Pass"
    detail = "Within advisory band."

    if eval_type == "qualitative":
        return {
            "status": "Review",
            "detail": "Document observations — qualitative checks rely on professional judgment.",
        }

    if value is None:
        return {"status": "Info", "detail": "Enter a numeric value to evaluate."}

    comparison_value = value
    if eval_type == "percentage_change":
        if baseline in (None, 0):
            return {
                "status": "Info",
                "detail": "Baseline or reference value is required to compute percent change.",
            }
        comparison_value = abs((value - baseline) / baseline) * 100
        detail = f"Computed change: {comparison_value:.2f}%"
    elif eval_type == "ratio":
        detail = f"Measured ratio: {comparison_value:.2f}"
    else:
        detail = f"Measured value: {comparison_value:.2f} {criterion.get('unit', '')}".strip()

    minimum = criterion.get("minimum")
    maximum = criterion.get("maximum")
    investigate_below = criterion.get("investigate_below")
    investigate_above = criterion.get("investigate_above")

    if minimum is not None and comparison_value < minimum:
        status = "Fail"
        detail += f" — below minimum of {minimum}."
    elif investigate_below is not None and comparison_value < investigate_below:
        status = "Investigate"
        detail += f" — below caution threshold of {investigate_below}."

    if maximum is not None and comparison_value > maximum:
        status = "Fail"
        detail += f" — above maximum of {maximum}."
    elif investigate_above is not None and comparison_value > investigate_above:
        status = "Investigate"
        detail += f" — above caution threshold of {investigate_above}."

    return {"status": status, "detail": detail}


def render_learning_card(test: Dict) -> None:
    cols = st.columns([2, 1])
    with cols[0]:
        st.subheader(test["name"])
        st.caption(f"Category: {test['category']} | Equipment: {', '.join(test['equipment'])}")
        st.write(test["summary"])
        st.markdown("**Purpose**")
        st.write(test["purpose"])
        st.markdown("**Procedure snapshot**")
        st.markdown("\n".join(f"- {step}" for step in test["procedure"]))
        st.markdown("**Result interpretation**")
        st.write(test["interpretation"])
        if test.get("kv_recommendations"):
            st.markdown("**Typical megohmmeter DC test selection**")
            kv_df = pd.DataFrame(test["kv_recommendations"]).rename(
                columns={
                    "max_rating_kv": "Nameplate ≤ kV",
                    "dc_test_kv": "Suggested DC test kV",
                    "example": "Typical asset",
                }
            )
            st.table(kv_df)
    with cols[1]:
        st.markdown("**Phases**")
        st.write(", ".join(test["phases"]))
        st.markdown("**Diagnostics cues**")
        st.write(f"Watch: {test['diagnostics']['watch']}")
        st.write(f"Investigate: {test['diagnostics']['investigate']}")
        st.write(f"Fail: {test['diagnostics']['fail']}")
        st.markdown("**Acceptance highlights**")
        for criterion in test["criteria"]:
            if criterion.get("evaluation_type") == "absolute":
                st.write(
                    f"- {criterion['label']}: {criterion.get('minimum', '—')} to {criterion.get('maximum', '—')} {criterion.get('unit', '')}"
                )
            else:
                st.write(
                    f"- {criterion['label']}: {criterion.get('note', 'Refer to calculator guidance for evaluation details.')}"
                )
        if test.get("result_implications"):
            st.markdown("**What the outcomes mean**")
            for status, meaning in test["result_implications"].items():
                st.write(f"{status}: {meaning}")

    render_deep_dive_section(test)


def render_learning_library(tests: List[Dict]) -> None:
    st.subheader("Test library")
    search = st.text_input("Filter by keyword, equipment, or category", placeholder="e.g., cable, power factor")
    phase = st.multiselect("Show phases", options=["Acceptance", "Maintenance"], default=["Acceptance", "Maintenance"])

    filtered = []
    for test in tests:
        haystack = " ".join(
            [
                test["name"],
                test["category"],
                " ".join(test["equipment"]),
                test["summary"],
            ]
        ).lower()
        matches_search = search.lower() in haystack if search else True
        matches_phase = any(ph in phase for ph in test["phases"])
        if matches_search and matches_phase:
            filtered.append(test)

    if not filtered:
        st.info("No tests match that filter. Try a broader search term.")
        return

    for test in filtered:
        st.divider()
        render_learning_card(test)


def render_pass_fail_calculator(index: Dict[str, Dict]) -> None:
    st.subheader("Pass / Investigate / Fail calculator")
    test_options = [(data["test"]["name"], crit_id) for crit_id, data in index.items()]
    test_label = st.selectbox(
        "Select the criterion to evaluate",
        options=[crit_id for _, crit_id in test_options],
        format_func=lambda crit_id: f"{index[crit_id]['test']['name']} — {index[crit_id]['criterion']['label']}",
    )
    test = index[test_label]["test"]
    criterion = index[test_label]["criterion"]

    voltage_context = None
    if test.get("kv_recommendations"):
        voltage_context = render_voltage_context(
            test, widget_suffix=f"calculator_{criterion['id']}"
        )

    col1, col2 = st.columns(2)
    measured_value = col1.number_input(
        f"Measured {criterion['parameter']} ({criterion.get('unit', '')})",
        value=0.0,
        format="%.3f",
    )
    baseline = None
    if criterion.get("evaluation_type") == "percentage_change":
        baseline = col2.number_input("Reference/baseline value", value=0.0, format="%.3f")
    elif criterion.get("evaluation_type") == "ratio":
        col2.info("Polarization Index ratios already normalize to the 1- and 10-minute readings.")
    else:
        col2.write(criterion.get("note", ""))

    result = evaluate_measurement(measured_value, criterion, baseline)

    status_color = {
        "Pass": "#0f9d58",
        "Investigate": "#fbbc04",
        "Fail": "#ea4335",
        "Info": "#5f6368",
        "Review": "#5f6368",
    }[result["status"]]

    st.markdown(
        f"""
        <div style="padding:1rem;border:1px solid {status_color};border-radius:0.5rem;">
            <h3 style="color:{status_color};margin-bottom:0;">{result['status']}</h3>
            <p style="margin-top:0.5rem;">{result['detail']}</p>
            <p style="font-size:0.9rem;">{criterion.get('note', '')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    meaning = describe_result_meaning(result["status"], test)
    if meaning:
        st.info(f"What this result means: {meaning}")

    if is_dga_test(test):
        render_dga_gas_breakdown(
            test,
            widget_suffix=f"calculator_{criterion['id']}",
            context_label="Calculator",
        )

    if voltage_context:
        st.caption(
            "Megohm readings are only comparable when the DC stress follows ANSI/NETA guidance. "
            "Use the voltage context inputs above to document the applied stress."
        )


def render_result_explorer(index: Dict[str, Dict]) -> None:
    st.subheader("Result explorer")
    selected = st.selectbox(
        "Choose a criterion to trend",
        options=list(index.keys()),
        format_func=lambda crit_id: f"{index[crit_id]['test']['name']} — {index[crit_id]['criterion']['label']}",
    )
    test = index[selected]["test"]
    criterion = index[selected]["criterion"]

    voltage_context = None
    if test.get("kv_recommendations"):
        voltage_context = render_voltage_context(
            test, widget_suffix=f"explorer_{criterion['id']}"
        )

    uploaded_file = st.file_uploader(
        "Upload measurement history (CSV or Excel)",
        type=("csv", "xlsx"),
        help=(
            "Include a numeric column for measurements and an optional timestamp column. "
            "Uploaded data replaces manual entry and simulation."
        ),
    )

    data_mode = st.radio(
        "Data source",
        ("Manual entry", "Simulate scenario"),
        horizontal=True,
        help="Paste your own measurements or generate representative samples to explore the logic.",
    )

    measurements: List[float] = []
    baseline: Optional[float] = None

    if data_mode == "Manual entry":
        default_values = format_series(_suggest_seed_values(criterion))
        raw_values = st.text_area(
            "Enter measurement values (latest last)",
            value=default_values,
            help="Separate numbers with commas, spaces, or line breaks.",
        )
        measurements, invalid_tokens = parse_measurement_series(raw_values)
        if invalid_tokens:
            st.warning(f"Ignored invalid entries: {', '.join(invalid_tokens)}")
        if criterion.get("evaluation_type") == "percentage_change":
            baseline = st.number_input(
                "Reference/baseline value for change calculation",
                value=100.0,
                format="%.3f",
            )
    else:
        scenario = st.select_slider(
            "Scenario severity",
            options=["Healthy", "Drifting", "Out of tolerance"],
            value="Drifting",
            help="Quickly visualize how data looks when it stays good, drifts, or exceeds a limit.",
        )
        sample_count = st.slider(
            "Number of simulated measurements",
            min_value=4,
            max_value=12,
            value=6,
        )
        measurements, baseline = simulate_measurements(
            criterion, scenario=scenario, count=sample_count
        )
        st.caption("Simulated measurement set (latest last)")
        st.code(format_series(measurements))
        if baseline is not None:
            st.caption(
                f"Baseline assumed for percent-change calculations: {baseline:.2f}"
            )

    timestamp_series: Optional[pd.Series] = None

    if uploaded_file:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                uploaded_df = pd.read_csv(uploaded_file)
            else:
                uploaded_df = pd.read_excel(uploaded_file)
        except (ValueError, FileNotFoundError) as exc:
            st.error(f"Could not read the uploaded file: {exc}")
            return

        if uploaded_df.empty:
            st.error("Uploaded file is empty. Provide at least one row of data.")
            return

        numeric_columns = [
            col for col in uploaded_df.columns if pd.api.types.is_numeric_dtype(uploaded_df[col])
        ]
        if not numeric_columns:
            st.error(
                "No numeric columns found. Ensure the file includes a measurement column."
            )
            return

        measurement_column = st.selectbox(
            "Select the measurement column",
            options=numeric_columns,
            key=f"measurement_column_{criterion['id']}",
        )
        timestamp_column = st.selectbox(
            "Select an optional timestamp column",
            options=["(None)"] + list(uploaded_df.columns),
            help="Use timestamps to label the chart, or leave blank to use row order.",
            key=f"timestamp_column_{criterion['id']}",
        )

        measurement_series = pd.to_numeric(
            uploaded_df[measurement_column], errors="coerce"
        )
        invalid_measurements = measurement_series.isna().sum()
        if invalid_measurements:
            st.warning(
                f"Ignored {invalid_measurements} non-numeric measurement rows in the upload."
            )
        measurement_series = measurement_series.dropna()
        if measurement_series.empty:
            st.error("No valid numeric measurements found after cleaning the upload.")
            return

        if timestamp_column != "(None)":
            timestamp_series = pd.to_datetime(
                uploaded_df[timestamp_column], errors="coerce"
            )
            timestamp_series = timestamp_series.loc[measurement_series.index]
            if timestamp_series.isna().any():
                st.warning(
                    "Dropped rows with invalid timestamps to keep the series aligned."
                )
            valid_mask = timestamp_series.notna()
            measurement_series = measurement_series.loc[valid_mask]
            timestamp_series = timestamp_series.loc[valid_mask]

            if measurement_series.empty:
                st.error(
                    "All rows were dropped after validating the timestamp column. Provide valid timestamps or clear the selection."
                )
                return

        measurements = measurement_series.reset_index(drop=True).tolist()

    if not measurements:
        st.warning("Provide at least one numeric value to generate insights.")
        return

    if criterion.get("evaluation_type") == "percentage_change" and baseline is None:
        baseline = st.number_input(
            "Reference/baseline value for change calculation",
            value=float(measurements[0]) if measurements else 0.0,
            format="%.3f",
        )

    df = pd.DataFrame({"Measurement": measurements})
    if timestamp_series is not None:
        df.insert(0, "Timestamp", timestamp_series.reset_index(drop=True))
    assessments = [
        evaluate_measurement(value, criterion, baseline) for value in measurements
    ]
    df["Assessment"] = [item["status"] for item in assessments]
    df["Insight"] = [item["detail"] for item in assessments]

    st.metric(
        label=f"Latest measurement ({criterion.get('unit', '').strip() or criterion['parameter']})",
        value=f"{measurements[-1]:.3f}",
        delta=(
            f"{measurements[-1] - measurements[0]:+.3f} vs first"
            if len(measurements) > 1
            else "0"
        ),
    )

    st.dataframe(df, use_container_width=True)

    chart_data = pd.DataFrame({"Measurement": measurements})
    if timestamp_series is not None:
        chart_data.index = timestamp_series.reset_index(drop=True)
    if criterion.get("evaluation_type") == "percentage_change" and baseline not in (None, 0):
        chart_data["Measurement"] = (
            (chart_data["Measurement"] - baseline).abs() / baseline
        ) * 100
        y_label = "Percent change"
    else:
        y_label = f"{criterion['parameter']} ({criterion.get('unit', '')})"

    st.line_chart(chart_data["Measurement"], height=240)
    st.caption(f"Y-axis: {y_label}")

    statuses = [item["status"] for item in assessments]
    details = [item["detail"] for item in assessments]
    severity, summary = summarize_series_outcome(
        measurements, statuses, details, criterion
    )
    renderer = {"error": st.error, "warning": st.warning, "success": st.success}[severity]
    renderer(summary)

    meaning = describe_result_meaning(statuses[-1], test)
    if meaning:
        st.info(
            f"Latest classification ({statuses[-1]}): {meaning}"
        )

    if is_dga_test(test):
        render_dga_gas_breakdown(
            test,
            widget_suffix=f"explorer_{criterion['id']}",
            context_label="Result explorer",
        )

    if voltage_context:
        st.caption(
            "Documenting the applied DC test voltage helps correlate insulation resistance trends year-over-year."
        )


def main() -> None:
    try:
        tests = load_test_library()
    except FileNotFoundError as exc:
        st.error(
            "Test library data file is missing. Add data/tests.json to continue."
        )
        st.info(str(exc))
        st.stop()
    except ValueError as exc:
        st.error("Test library data could not be loaded. Fix the data file and retry.")
        st.info(str(exc))
        st.stop()

    criteria_index = build_criteria_index(tests)

    st.title("ANSI-NETA MTS 2023 Learning Lab")
    st.write(
        "This interactive workspace summarizes common test families from the ANSI/NETA MTS 2023 standard. "
        "It is strictly for education — always consult the official publication for contractual decisions."
    )
    st.write(
        "The current library focuses on the components most critical to utility-scale solar facilities: generator step-up "
        "transformers, collector breakers, and metal-clad switchgear."
    )
    st.info(
        "Use the tabs below to review test expectations, experiment with sample data, and assess field results. "
        "Values represent typical industry ranges inspired by ANSI/NETA experience and should be validated for each project."
    )

    tab_intro, tab_library, tab_explorer, tab_calculator, tab_notes = st.tabs(
        [
            "Start",
            "Test Library",
            "Result Explorer",
            "Calculator",
            "Notes",
        ]
    )

    with tab_intro:
        st.header("How to use this learning lab")
        st.markdown(
            """
            1. **Study** — Browse the Test Library to review intent, procedures, and qualitative cues.
            2. **Explore** — Paste recent measurements into the Result Explorer to visualize trends.
            3. **Decide** — Use the Calculator to quickly classify a reading as Pass, Investigate, or Fail.

            The workflows mirror a typical maintenance report review meeting where the engineer needs to interpret
            data without having the ANSI/NETA book in front of them.
            """
        )
        st.warning(
            "Educational copy only. Replace the embedded rule-of-thumb limits with project-specific values before issuing reports."
        )

    with tab_library:
        render_learning_library(tests)

    with tab_explorer:
        render_result_explorer(criteria_index)

    with tab_calculator:
        render_pass_fail_calculator(criteria_index)

    with tab_notes:
        st.subheader("Implementation notes & references")
        st.write(
            "The values used here are paraphrased summaries that point users toward the appropriate sections of ANSI/NETA MTS 2023. "
            "Always verify with manufacturer data, safety rules, and calibrated instruments."
        )
        st.markdown(
            "- **Color coding** follows the familiar green/yellow/red decision tree used in many maintenance reports.\n"
            "- **Percentage change rules** assume the user supplies a certified reference (factory, nameplate, or best historical value).\n"
            "- **Trend explorer** is a lightweight sandbox — export CSVs from your test set to perform deeper analytics."
        )
        st.success(
            "Looking for something specific? Let us know what additional tests or workflows you would like to see, and we can extend the library."
        )


if __name__ == "__main__":
    main()
