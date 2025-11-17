# ANSI-NETA MTS 2023 Learning Lab

This repository hosts a Streamlit application that provides an interactive, educational view of ANSI/NETA MTS 2023 maintenance testing practices. The goal is to help engineers explore common electrical tests, learn how to interpret measured values, and practice pass/fail decision making without reproducing the standard.  The curated content prioritizes the equipment that dominates utility-scale solar plants (generator step-up transformers, collector breakers, switchgear lineups, etc.) so design and operations engineers can focus on the data they review most often.

## Features
- Curated learning cards for frequently referenced ANSI/NETA MTS test families, with emphasis on transformer, circuit breaker, and switchgear diagnostics for PV facilities.
- Search and filtering tools to quickly locate applicable procedures by equipment type.
- Interactive calculator that classifies entered field results as **Pass**, **Investigate**, or **Fail** according to rule-of-thumb ranges inspired by ANSI/NETA guidance.
- Result explorer that plots manual entries or simulated scenarios and surfaces explicit trend/triage summaries so engineers know exactly what to do with the data.
- Built-in contextual help, references, and caution statements to reinforce safe, standards-based use.
- Expanded insulation-resistance module with ANSI/NETA-style DC test-voltage tables plus “what it means” explanations so megohm readings translate into actionable maintenance decisions.
- Every learning card now carries plain-language Pass/Investigate/Fail implications so engineers instantly know the operational risk tied to their calculator result.
- Deep-dive expanders on the most-used solar plant tests (visual inspection, insulation resistance, contact resistance, power factor, breaker diagnostics, transformer health, and switchgear withstand) provide PV-specific quick references, interpretation cues, and remediation playbooks.
- Transformer DGA workflows now surface IEEE C57.104 / IEC 60599 key-gas thresholds (including CO/CO₂ paper-health cues) directly inside the calculator and result explorer so each gas reading comes with immediate “what this means” context.

### Simulate measurements before heading to the field
- Within the **Result Explorer** tab, choose **Simulate scenario** to auto-populate realistic samples (Healthy, Drifting, or Out of tolerance) for any criterion.
- Review the generated metric, table, and insight banner to understand how marginal data will be classified before you ever step on site.
- Switch back to **Manual entry** to paste your own test set and confirm whether the resulting insight remains actionable.

### Insulation resistance deep dive
- Learning cards now display a megohmmeter voltage-selection table that mirrors the ANSI/NETA quick reference, plus the consequences of Pass/Investigate/Fail outcomes.
- The calculator and result explorer ask for the equipment nameplate kV and applied DC test voltage so you can verify that readings were taken at the proper stress level.
- Result summaries now include reasoning statements (e.g., “moisture likely present” or “keep the asset de-energized”) to help engineers plan the next field action.
- The same insight pattern has been extended across transformer, breaker, and switchgear learning cards so the interpretation experience stays consistent regardless of the test family.
- Additional learning-card deep dives outline PV-centric decision clues for contact resistance, power factor, breaker timing/primary injection, transformer ratio/resistance/DGA, and switchgear withstand so users know how to respond when data shifts.
- The transformer DGA card highlights IEEE C57.104 and IEC 60599 guidance, complete with per-gas entry fields that explain how hydrogen, methane, ethane, ethylene, acetylene, carbon monoxide, and carbon dioxide trends tie back to actionable remediation steps.

## Running the app
1. Install the dependencies (ideally inside a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```
2. Launch Streamlit:
   ```bash
   streamlit run streamlit_app.py
   ```

The app is designed strictly for educational use and does not replace the ANSI/NETA MTS 2023 publication. Always refer to the official document for contractual or compliance decisions.
