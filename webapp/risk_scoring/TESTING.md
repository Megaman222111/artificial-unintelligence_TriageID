# How to test risk scoring (CSV-trained model, DB inference)

All commands assume you are in the `webapp` directory.

## 1. Install dependencies

```bash
cd webapp
pip install -r requirements.txt
```

If you run frontend locally too:

```bash
cd webapp/frontend
npm install
```

## 2. Ensure training CSV exists

Default CSV path:

`webapp/risk_scoring/data/diabetic_data.csv`

## 3. Train model from CSV

```bash
cd webapp
python manage.py train_risk_model --min-rows 25 --min-positives 5 --max-rows 50000
```

Optional custom CSV path:

```bash
cd webapp
python manage.py train_risk_model --csv-path /absolute/path/to/diabetic_data.csv --max-rows 0
```

Output includes model version, row count, positives, and metrics.
Model artifact is saved in `webapp/risk_scoring/artifacts/risk_model_risk-v1-*.joblib`.

## 4. Test API risk scoring

Start Django:

```bash
cd webapp
python manage.py runserver
```

In another terminal:

```bash
API_BASE="http://127.0.0.1:8000"

PATIENT_ID=$(
  curl -s "$API_BASE/api/patients/" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')"
)

if [ -z "$PATIENT_ID" ]; then
  echo "No patients found. Create one first, then retry."
else
  echo "Using patient_id=$PATIENT_ID"
  curl -s -X POST "$API_BASE/api/patients/risk-score/" \
    -H "Content-Type: application/json" \
    -d "{\"patient_id\":\"$PATIENT_ID\"}" | python3 -m json.tool
fi
```

You should get: `riskBand`, `riskProbability`, `modelVersion`, `topFactors`, `scoringMode`.

## 5. Full stack check

Backend:

```bash
cd webapp
python manage.py runserver
```

Frontend:

```bash
cd webapp/frontend
npm run dev
```

Open a patient in the UI and verify risk data is displayed.
