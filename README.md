# ANSI-NETA MTS 2023 Learning Lab

This repository hosts a Streamlit application that provides an interactive, educational view of ANSI/NETA MTS 2023 maintenance testing practices. The goal is to help engineers explore common electrical tests, learn how to interpret measured values, and practice pass/fail decision making without reproducing the standard.  The curated content prioritizes the equipment that dominates utility-scale solar plants (generator step-up transformers, collector breakers, switchgear lineups, etc.) so design and operations engineers can focus on the data they review most often.

## Features
- Curated learning cards for frequently referenced ANSI/NETA MTS test families, with emphasis on transformer, circuit breaker, and switchgear diagnostics for PV facilities.
- Search and filtering tools to quickly locate applicable procedures by equipment type.
- Interactive calculator that classifies entered field results as **Pass**, **Investigate**, or **Fail** according to rule-of-thumb ranges inspired by ANSI/NETA guidance.
- Result explorer that plots manual entries or simulated scenarios and surfaces explicit trend/triage summaries so engineers know exactly what to do with the data.
- Built-in contextual help, references, and caution statements to reinforce safe, standards-based use.

### Simulate measurements before heading to the field
- Within the **Result Explorer** tab, choose **Simulate scenario** to auto-populate realistic samples (Healthy, Drifting, or Out of tolerance) for any criterion.
- Review the generated metric, table, and insight banner to understand how marginal data will be classified before you ever step on site.
- Switch back to **Manual entry** to paste your own test set and confirm whether the resulting insight remains actionable.

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
