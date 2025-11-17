"""Streamlit learning lab for ANSI/NETA MTS 2023."""
from __future__ import annotations

from collections import Counter
import random
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ANSI-NETA MTS 2023 Learning Lab",
    layout="wide",
    page_icon="⚡",
)


def _build_test_library() -> List[Dict]:
    """Curated reference data for learning cards."""
    return [
        {
            "id": "visual_inspection",
            "name": "Visual & Mechanical Inspection",
            "category": "Foundational",
            "summary": "Systematic inspection that verifies nameplate data, mechanical security, clearances, and safety interlocks before energized tests.",
            "equipment": [
                "Switchgear",
                "Transformers",
                "Protective relays",
                "Battery systems",
            ],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Detects obvious defects that can invalidate subsequent electrical tests.",
            "procedure": [
                "Confirm lockout/tagout and discharge stored energy.",
                "Inspect insulation surfaces, CT/PT polarities, shutters, and arc barriers.",
                "Verify bolted connections for torque paint movement or discoloration.",
                "Document nameplate data, as-left settings, and any deviations.",
            ],
            "interpretation": "Findings are qualitative; anything unsafe or not per drawings requires correction before energizing.",
            "criteria": [
                {
                    "id": "visual_no_damage",
                    "label": "No visible damage or contamination",
                    "parameter": "Condition",
                    "unit": "n/a",
                    "evaluation_type": "qualitative",
                    "investigate_note": "Any evidence of overheating, tracking, or loose hardware mandates corrective action.",
                }
            ],
            "diagnostics": {
                "watch": "Minor dust or labeling gaps — clean and update records.",
                "investigate": "Staining, insulation cracks, bent buswork, or missing bolting hardware.",
                "fail": "Active oil leaks, structural damage, or compromised barriers.",
            },
            "result_implications": {
                "Review": (
                    "Document every deficiency and correct or defer it with engineering approval before any energized testing "
                    "because visual issues often foreshadow electrical failures."
                ),
                "default": (
                    "Use the inspection findings to prioritize mechanical repairs that remove safety hazards and contamination "
                    "pathways before energizing equipment."
                ),
            },
        },
        {
            "id": "insulation_resistance",
            "name": "Insulation Resistance (Megohmmeter)",
            "category": "Dielectric",
            "summary": "High-resistance measurement that validates the health of solid insulation systems.",
            "equipment": [
                "Cables",
                "Transformers",
                "Switchgear",
                "Motors",
            ],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Baseline integrity check to detect moisture, contamination, or insulation damage.",
            "procedure": [
                "Apply the manufacturer/ANSI recommended DC test voltage for 1 minute.",
                "Record 1-minute, 10-minute, and polarization index (PI) values.",
                "Demagnetize large machines or windings after testing.",
            ],
            "interpretation": "ANSI/NETA focuses on trending: stable or increasing values are acceptable while decreasing results trigger investigation.",
            "kv_recommendations": [
                {"max_rating_kv": 1.0, "dc_test_kv": 1.0, "example": "Control wiring, LV motors"},
                {"max_rating_kv": 5.0, "dc_test_kv": 2.5, "example": "1–5 kV cables"},
                {"max_rating_kv": 15.0, "dc_test_kv": 5.0, "example": "5–15 kV switchgear"},
                {"max_rating_kv": 34.5, "dc_test_kv": 10.0, "example": "Collector feeders"},
                {"max_rating_kv": 69.0, "dc_test_kv": 15.0, "example": "GSU tertiary"},
                {"max_rating_kv": 138.0, "dc_test_kv": 25.0, "example": "HV transmission windings"},
            ],
            "criteria": [
                {
                    "id": "ir_mv_cable",
                    "label": "MV cable > 5 kV (1-min value)",
                    "parameter": "Resistance",
                    "unit": "MΩ",
                    "evaluation_type": "absolute",
                    "minimum": 100,
                    "investigate_below": 200,
                    "note": "Below 100 MΩ is typically rejected; 100–200 MΩ demands cleaning/drying review.",
                },
                {
                    "id": "ir_motor_pi",
                    "label": "Rotating machine PI",
                    "parameter": "PI ratio",
                    "unit": "ratio",
                    "evaluation_type": "ratio",
                    "minimum": 2.0,
                    "investigate_below": 3.0,
                    "note": "PI < 2 suggests moisture/contamination for Class F or better insulation systems.",
                },
                {
                    "id": "ir_switchgear_bus",
                    "label": "Metal-clad switchgear bus (5–15 kV)",
                    "parameter": "Resistance",
                    "unit": "MΩ",
                    "evaluation_type": "absolute",
                    "minimum": 200,
                    "investigate_below": 400,
                    "note": "Values <200 MΩ usually fail maintenance criteria; 200–400 MΩ needs cleaning/drying before energizing.",
                },
                {
                    "id": "ir_gsu_winding",
                    "label": "GSU HV winding to ground",
                    "parameter": "Resistance",
                    "unit": "MΩ",
                    "evaluation_type": "absolute",
                    "minimum": 1000,
                    "investigate_below": 1500,
                    "note": "Healthy generator step-up windings trend in the multi-gigaohm range; <1 GΩ indicates wet paper or carbon tracking.",
                },
            ],
            "diagnostics": {
                "watch": "Gradual decline in PI or IR yet still above acceptance — schedule retest.",
                "investigate": "Drop of >25% from baseline or absolute IR < investigate threshold.",
                "fail": "IR below minimum or unstable readings that never stabilize.",
            },
            "result_implications": {
                "Pass": "High megohm values indicate the solid insulation is dry and contaminants are not providing parallel leakage paths.",
                "Investigate": "Borderline resistance often points to moisture absorption, carbonized surfaces, or lead dress issues that require cleaning or re-drying before energizing.",
                "Fail": "A failed megohm test signifies insulation breakdown — energizing risks flashover, so keep the asset de-energized until insulation is repaired and re-tested.",
            },
        },
        {
            "id": "contact_resistance",
            "name": "Contact Resistance (Micro-ohm)",
            "category": "Conductor Integrity",
            "summary": "Low-resistance measurement across bolted or moving current-carrying joints to verify cleanliness and pressure.",
            "equipment": ["Switchgear", "Bus duct", "Circuit breakers"],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Identifies loose connections that create heating or unequal current sharing.",
            "procedure": [
                "Inject ≥100 A DC using a DLRO across each phase joint.",
                "Compare readings phase-to-phase and against manufacturer baseline.",
                "Record ambient temperature for trending adjustments.",
            ],
            "interpretation": "Consistency is critical; ANSI/NETA highlights a 50% maximum spread between phases or 50 µΩ absolute limit for many bus joints.",
            "criteria": [
                {
                    "id": "cr_switchgear",
                    "label": "Metal-clad switchgear main bus",
                    "parameter": "Resistance",
                    "unit": "µΩ",
                    "evaluation_type": "absolute",
                    "maximum": 100,
                    "investigate_above": 75,
                    "note": "Readings >100 µΩ typically fail; >75 µΩ suggests re-torque/cleaning.",
                },
                {
                    "id": "cr_pct_delta",
                    "label": "Phase balance delta",
                    "parameter": "Percent deviation",
                    "unit": "%",
                    "evaluation_type": "percentage_change",
                    "maximum": 50,
                    "investigate_above": 30,
                    "note": "More than 50% deviation from the average indicates unacceptable imbalance.",
                },
            ],
            "diagnostics": {
                "watch": "Slight imbalance that repeats between outages.",
                "investigate": "Any single joint drifting upward more than 20 µΩ per maintenance cycle.",
                "fail": "Contacts exceeding published limits even after maintenance.",
            },
            "result_implications": {
                "Pass": "Uniform micro-ohm readings confirm bolted joints and breaker contacts are tight enough to avoid localized heating during peak output.",
                "Investigate": "Elevated resistance usually means oxide buildup or insufficient torque — clean, re-torque, and remeasure before returning to service.",
                "Fail": "High contact resistance will overheat and can trigger arcing, so keep the equipment de-energized until the joint or breaker is refurbished.",
            },
        },
        {
            "id": "power_factor",
            "name": "Insulation Power Factor / Tan Delta",
            "category": "Dielectric",
            "summary": "AC loss measurement expressing watts lost versus volt-amperes applied across insulation.",
            "equipment": ["Transformers", "Bushings", "Rotating machines"],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Highlights insulation aging, contamination, or moisture ingress.",
            "procedure": [
                "Energize winding or component using a power-factor test set at line frequency.",
                "Record hot-corrected (CH) and 10-kV readings when applicable.",
                "Compare to nameplate limits or previous test seasons.",
            ],
            "interpretation": "ANSI/NETA publishes maximum percent power-factor/tan-delta per equipment class.",
            "criteria": [
                {
                    "id": "pf_transformer",
                    "label": "Transformer CH power factor",
                    "parameter": "Percent",
                    "unit": "%",
                    "evaluation_type": "absolute",
                    "maximum": 1.0,
                    "investigate_above": 0.5,
                    "note": "Values between 0.5–1.0% prompt drying review; >1.0% is typically rejected for new equipment.",
                },
                {
                    "id": "pf_bushing",
                    "label": "Bushing PF change",
                    "parameter": "Percent change",
                    "unit": "%",
                    "evaluation_type": "percentage_change",
                    "maximum": 50,
                    "investigate_above": 25,
                    "note": "Change >50% from nameplate/certified value fails.",
                },
            ],
            "diagnostics": {
                "watch": "Stable but elevated PF with no change year-over-year.",
                "investigate": "Sudden 10% relative jump versus prior season.",
                "fail": "PF beyond absolute limits or trending upward every cycle despite maintenance.",
            },
            "result_implications": {
                "Pass": "Low dielectric loss confirms the insulation is dry and capacitive currents are within ANSI/NETA expectations.",
                "Investigate": "Rising losses often precede insulation breakdown — plan oil processing, drying, or more frequent monitoring before energizing at full voltage.",
                "Fail": "High power factor indicates active insulation deterioration, so keep the asset out of service until the root cause (moisture, contamination, aging) is corrected.",
            },
        },
        {
            "id": "breaker_timing",
            "name": "Circuit Breaker Timing & Motion",
            "category": "Protection",
            "summary": "Measures opening/closing speed and pole synchronism for medium-voltage circuit breakers.",
            "equipment": ["MV circuit breakers"],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Verifies stored-energy mechanisms operate fast enough to clear faults and minimize stress on equipment.",
            "procedure": [
                "Connect travel transducers or motion analyzers to each pole.",
                "Perform close, open, and close-open sequences capturing time stamps.",
                "Compare results to manufacturer tolerance tables.",
            ],
            "interpretation": "ANSI/NETA references manufacturer tolerances; typical medium-voltage air breakers must open within 50–80 ms and poles should be within 2 ms of each other.",
            "criteria": [
                {
                    "id": "cb_open_time",
                    "label": "Open time",
                    "parameter": "Milliseconds",
                    "unit": "ms",
                    "evaluation_type": "absolute",
                    "maximum": 80,
                    "investigate_above": 70,
                    "note": "Values >80 ms fail; 70–80 ms justify spring/exhaust inspection.",
                },
                {
                    "id": "cb_pole_sync",
                    "label": "Pole timing difference",
                    "parameter": "Delta",
                    "unit": "ms",
                    "evaluation_type": "absolute",
                    "maximum": 2,
                    "investigate_above": 1,
                    "note": "Poles drifting >2 ms apart can damage equipment and usually fail.",
                },
            ],
            "diagnostics": {
                "watch": "Slightly slow close time that repeats.",
                "investigate": "Any drift correlated with lubricant age or counter readings.",
                "fail": "Out-of-tolerance timing or poles not completing travel.",
            },
            "result_implications": {
                "Pass": "Mechanism speeds are fast enough to interrupt PV collector faults within the modeled coordination times.",
                "Investigate": "Approaching the limit often signals weak springs or sticky linkages — service the operator before relying on it for high-current clearing.",
                "Fail": "Slow or unsynchronized poles cannot clear faults safely and risk equipment damage, so remove the breaker from service until rebuilt.",
            },
        },
        {
            "id": "transformer_ttr",
            "name": "Transformer Turns Ratio (TTR)",
            "category": "Transformer Core",
            "summary": "Confirms the proper ratio and vector group for generator step-up and station service transformers used in PV plants.",
            "equipment": ["GSU transformers", "Pad-mount transformers"],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Avoids energizing a mismatched winding connection that would distort voltage or overload inverters.",
            "procedure": [
                "Isolate and ground the transformer, remove surge arresters and PT fuses.",
                "Apply the TTR test set per winding and record ratio, phase displacement, and excitation current.",
                "Compare readings phase-by-phase to the certified factory test sheet.",
            ],
            "interpretation": "ANSI/NETA tolerances are tight (±0.5%) for new equipment; solar inverters depend on this accuracy to stay within grid codes.",
            "criteria": [
                {
                    "id": "ttr_ratio_dev",
                    "label": "Ratio deviation from nameplate",
                    "parameter": "Percent deviation",
                    "unit": "%",
                    "evaluation_type": "absolute",
                    "maximum": 0.5,
                    "investigate_above": 0.3,
                    "note": "Deviation above 0.5% typically fails acceptance tests for power transformers.",
                },
                {
                    "id": "ttr_phase_shift",
                    "label": "Phase shift difference",
                    "parameter": "Degrees",
                    "unit": "°",
                    "evaluation_type": "absolute",
                    "maximum": 0.5,
                    "investigate_above": 0.25,
                    "note": "Unexpected displacement hints at miswired taps or incorrect vector group.",
                },
            ],
            "diagnostics": {
                "watch": "Slight deviation confined to one tap position.",
                "investigate": "Ratios drifting on multiple phases after transport or repairs.",
                "fail": "Any ratio or phase shift outside ANSI/NETA tolerance.",
            },
            "result_implications": {
                "Pass": "Measured ratios align with nameplate values so inverters will deliver grid-compliant voltage.",
                "Investigate": "Minor deviation can stem from tap-changer misalignment or loosened leads — correct and retest before energizing.",
                "Fail": "Significant ratio or vector errors indicate winding damage or misconnections that would create unacceptable voltage and circulating currents, so keep the transformer offline.",
            },
        },
        {
            "id": "winding_resistance",
            "name": "Transformer Winding Resistance",
            "category": "Transformer Core",
            "summary": "DC resistance check that validates winding integrity, tap-changer contacts, and soldered joints.",
            "equipment": ["GSU transformers", "Station service transformers"],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Detects loose connections that would otherwise overheat when solar generation surges each morning.",
            "procedure": [
                "Demagnetize the core, connect a Kelvin bridge, and measure each phase on every tap.",
                "Record ambient and winding temperatures to correct to the reference temperature.",
                "Compare each phase against the factory baseline or previous outage.",
            ],
            "interpretation": "Percent change from the certified baseline is more important than the absolute ohmic value for large transformers.",
            "criteria": [
                {
                    "id": "wr_pct_dev",
                    "label": "Percent deviation from baseline",
                    "parameter": "Percent change",
                    "unit": "%",
                    "evaluation_type": "percentage_change",
                    "maximum": 10,
                    "investigate_above": 5,
                    "note": ">10% suggests damaged leads or LTC contacts; schedule outage before peak season.",
                }
            ],
            "diagnostics": {
                "watch": "Slow drift that correlates with LTC maintenance cycles.",
                "investigate": "Phase-to-phase imbalance greater than 5% even after temperature correction.",
                "fail": "Deviation above 10% or unstable readings that never settle.",
            },
            "result_implications": {
                "Pass": "Balanced DC ohms confirm winding joints, leads, and LTC contacts are intact so load current will share evenly.",
                "Investigate": "Increasing imbalance suggests carbon on tap-changer contacts or loose brazed joints — correct the mechanical issue before loading the transformer.",
                "Fail": "Large deviations or opens show a compromised winding path that will overheat immediately; keep the transformer de-energized until repaired and retested.",
            },
        },
        {
            "id": "transformer_dga",
            "name": "Transformer Dissolved Gas Analysis",
            "category": "Insulating Fluids",
            "summary": "Laboratory test of oil samples to identify incipient faults in GSU transformers and PV collector banks.",
            "equipment": ["Oil-filled transformers"],
            "phases": ["Maintenance"],
            "purpose": "Provides early warning of thermal or electrical defects before a forced outage on the solar plant.",
            "procedure": [
                "Pull sealed oil samples using clean syringes following ASTM D923.",
                "Analyze gases per ASTM D3612 and trend CO, C2H2, C2H4, CH4, and H2.",
                "Compare total dissolved combustible gas (TDCG) to IEEE C57.104/NETA action levels.",
            ],
            "interpretation": "Action levels dictate whether to increase sampling frequency, schedule an outage, or remove the unit from service.",
            "criteria": [
                {
                    "id": "dga_tdcg",
                    "label": "Total dissolved combustible gas",
                    "parameter": "Concentration",
                    "unit": "ppm",
                    "evaluation_type": "absolute",
                    "maximum": 7200,
                    "investigate_above": 3600,
                    "note": ">7200 ppm typically triggers immediate outage planning per IEEE C57.104 Table 2.",
                }
            ],
            "diagnostics": {
                "watch": "TDCG trending upward but still <1800 ppm.",
                "investigate": "Level 3 condition (3600–7200 ppm) or rapid gas growth.",
                "fail": "Level 4 gas concentration or confirmed arcing signature.",
            },
            "result_implications": {
                "Pass": "Gas levels align with normal aging so the transformer can stay in service with routine monitoring.",
                "Investigate": "Elevated TDCG or accelerating key-gas growth implies developing faults — increase sampling and plan targeted electrical tests before peak season.",
                "Fail": "Condition 4 concentrations indicate an active fault; schedule an outage immediately to avoid catastrophic failure.",
            },
        },
        {
            "id": "breaker_primary",
            "name": "Circuit Breaker Primary Injection",
            "category": "Protection",
            "summary": "High-current test that verifies medium-voltage collector breakers trip within their coordination band.",
            "equipment": ["MV circuit breakers", "PV collector breakers"],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Ensures faults on PV feeders clear locally without tripping upstream transmission breakers.",
            "procedure": [
                "Connect a primary injection set to each pole and inject current to pickup and time-delay points.",
                "Capture actual trip time, pickup current, and relay target operations.",
                "Compare against relay settings and manufacturer curves.",
            ],
            "interpretation": "Pickup current and operating time must align with the relay's programmed curve to maintain coordination between PV inverters and utility protection.",
            "criteria": [
                {
                    "id": "breaker_pickup_delta",
                    "label": "Pickup current deviation",
                    "parameter": "Percent change",
                    "unit": "%",
                    "evaluation_type": "percentage_change",
                    "maximum": 15,
                    "investigate_above": 10,
                    "note": "Pickup outside ±15% of the setpoint indicates CT polarity or relay issues.",
                },
                {
                    "id": "breaker_trip_time",
                    "label": "Trip time (long-delay point)",
                    "parameter": "Milliseconds",
                    "unit": "ms",
                    "evaluation_type": "absolute",
                    "maximum": 130,
                    "investigate_above": 110,
                    "note": "Values slower than programmed curve reduce clearing coordination.",
                },
            ],
            "diagnostics": {
                "watch": "Minor pickup shift correlated with relay firmware updates.",
                "investigate": "Trip times creeping toward coordination margins on feeder breakers feeding large PV blocks.",
                "fail": "Breaker fails to trip or exceeds the published tolerance.",
            },
            "result_implications": {
                "Pass": "Protection elements respond within tolerance so PV feeder faults will clear where intended.",
                "Investigate": "Out-of-band pickup or timing usually signals misadjusted relays or mechanical drag — correct settings and re-test before energizing the feeder.",
                "Fail": "A breaker that cannot interrupt current or trips late endangers upstream equipment; keep it tagged out until repaired or replaced.",
            },
        },
        {
            "id": "switchgear_hipot",
            "name": "Switchgear AC Withstand / Hi-Pot",
            "category": "Switchgear",
            "summary": "Dielectric test on metal-clad switchgear lineups that house PV inverter feeder breakers.",
            "equipment": ["Metal-clad switchgear", "Collector switchgear"],
            "phases": ["Acceptance", "Maintenance"],
            "purpose": "Demonstrates that primary insulation and bus supports can withstand overvoltages before energizing feeders.",
            "procedure": [
                "Remove surge devices, isolate control wiring, and apply the ANSI/NETA recommended AC withstand voltage.",
                "Hold the test voltage (typically 27 kV for 15 kV-class gear) for 1 minute while monitoring leakage current.",
                "Document leakage current, audible discharge, and partial discharge observations.",
            ],
            "interpretation": "Any puncture or rapid increase in leakage current indicates contaminated insulation that must be addressed before returning solar feeders to service.",
            "criteria": [
                {
                    "id": "switchgear_ac_withstand",
                    "label": "Applied withstand voltage",
                    "parameter": "Voltage",
                    "unit": "kV rms",
                    "evaluation_type": "absolute",
                    "minimum": 27,
                    "investigate_below": 24,
                    "note": "15 kV-class gear should hold 27 kV for one minute during acceptance tests.",
                }
            ],
            "diagnostics": {
                "watch": "Slightly rising leakage current that stabilizes before test end.",
                "investigate": "Surface tracking, audible discharge, or inability to reach full voltage.",
                "fail": "Flashover, collapse of voltage, or leakage exceeding manufacturer limit.",
            },
            "result_implications": {
                "Pass": "The gear can withstand rated overvoltages, indicating bus insulation is clean and intact.",
                "Investigate": "Higher leakage or audible partial discharge suggests contamination or voids — clean, dry, and reinspect before energizing.",
                "Fail": "Dielectric breakdown proves the insulation will not survive service stress; repair or replace the cell before re-energizing.",
            },
        },
    ]


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

    if not measurements:
        st.warning("Provide at least one numeric value to generate insights.")
        return

    df = pd.DataFrame({"Measurement": measurements})
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

    chart_data = df.copy()
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

    if voltage_context:
        st.caption(
            "Documenting the applied DC test voltage helps correlate insulation resistance trends year-over-year."
        )


def main() -> None:
    tests = _build_test_library()
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
