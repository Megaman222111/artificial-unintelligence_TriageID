# Risk model – external training dataset

The risk model can be trained on an external dataset that matches our feature schema. The dataset used for training (when not using your own DB) is:

## Dataset: Diabetes 130-US Hospitals for Years 1999–2008

- **Source:** UCI Machine Learning Repository  
- **URL:** https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008  
- **Citation:** Beata Strack, Jonathan P. DeShazo, Chris Gennings, Juan L. Olmo, Sebastian Ventura, Krzysztof J. Cios, and John N. Clore, “Impact of HbA1c Measurement on Hospital Readmission Rates: Analysis of 70,000 Clinical Database Patient Records,” *BioMed Research International*, vol. 2014, Article ID 781670, 11 pages, 2014.  
- **License:** CC BY 4.0  

### Contents

- **~101,766** inpatient encounters (diabetes patients) from 130 US hospitals (1999–2008).
- **Outcome used for risk:** 30-day readmission (`readmitted == '<30'` → high risk; otherwise low risk).
- **Features mapped to our schema:**
  - `age_years` ← age bracket midpoint
  - `days_since_admission` ← `time_in_hospital`
  - `medication_count` ← `num_medications`
  - `history_count` ← `number_diagnoses`
  - `past_history_count` ← `number_inpatient + number_outpatient + number_emergency`
  - `gender` ← `gender`
  - `blood_type` ← `"unknown"` (not in dataset)
  - `status` ← `"active"`
  - `insurance_mode` ← `"insurance"`
  - `text` ← `diag_1`, `diag_2`, `diag_3`, `diabetesMed`, `change` concatenated
  - `allergy_count`, `prescription_count` ← 0 (not in dataset)

### How to train with this dataset

1. **Automatic download** (script downloads the zip from UCI if the CSV is missing):

   ```bash
   cd webapp
   PYTHONPATH=. python risk_scoring/train_from_uci_dataset.py
   ```

2. **Using a local CSV:**  
   Place `diabetic_data.csv` in `webapp/risk_scoring/data/`. The script will use it and skip the download.

The trained model is saved under `webapp/risk_scoring/artifacts/risk_model_*.joblib` and is used by the risk scoring service for “low” / “medium” / “high” risk.
