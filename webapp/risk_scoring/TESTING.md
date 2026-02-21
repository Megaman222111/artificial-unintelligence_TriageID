# How to test risk scoring

All commands assume you are in the **webapp** directory: `cd webapp` (or `cd path/to/hacked-2025/webapp`).

---

## 1. Install dependencies

```bash
cd webapp
pip install -r requirements.txt
```

If you run the **frontend** too, install Node deps:

```bash
cd webapp/frontend
npm install
```

---

## 2. Test the model (no Django, no server)

This loads the trained model and runs one prediction. No database or server needed.

```bash
cd webapp
PYTHONPATH=. python risk_scoring/test_risk_service.py
```

You should see something like:

- `OK – risk scoring works`
- `risk_band: low` or `medium` or `high`
- `risk_probability: 0.xxxx`
- `model_version: uci-simple-50000rows-5587pos`
- `scoring_mode: supervised`

If you see “No risk_model_*.joblib”, train first (step 4 below).

If you see **"Can't get attribute '_RemainderColsList'"** or **InconsistentVersionWarning** (different scikit-learn version), the saved model was built with another sklearn release. Retrain to create a compatible model: run step 4 below.

---

## 3. Test the API (Django backend only)

Start Django, then call the risk-score endpoint with a real patient ID.

**Terminal 1 – start Django:**

```bash
cd webapp
python manage.py runserver
```

**Terminal 2 – get a patient ID, then request risk score:**

```bash
# List patients and copy an id from the JSON
curl -s http://127.0.0.1:8000/api/patients/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else 'no patients')"

# Replace YOUR_PATIENT_ID with the printed id, then:
curl -s -X POST http://127.0.0.1:8000/api/patients/risk-score/ \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "YOUR_PATIENT_ID"}' | python3 -m json.tool
```

You should get JSON with `riskBand`, `riskProbability`, `modelVersion`, `topFactors`, `scoringMode`.

If you have no patients, create one via the frontend or admin, or use the create endpoint.

---

## 4. Train the model (if you don’t have a model yet)

UCI dataset is used. CSV is loaded from `webapp/risk_scoring/data/diabetic_data.csv`; if missing, the script will try to download it.

```bash
cd webapp
PYTHONPATH=. python risk_scoring/train_from_uci_dataset.py
```

Model is saved under `webapp/risk_scoring/artifacts/risk_model_*.joblib`. Then re-run step 2 or 3.

---

## 5. Full stack: backend + frontend (scan flow)

**Terminal 1 – Django:**

```bash
cd webapp
python manage.py runserver
```

**Terminal 2 – Next.js frontend:**

```bash
cd webapp/frontend
npm run dev
```

Open the app in the browser (e.g. http://localhost:3000). Log in if required, then:

- Use the NFC scan flow (or whatever opens a patient), or
- Go to a patient in the dashboard and open their detail/overlay.

The UI will call the risk-score API and show **low** / **medium** / **high** and the probability.

Ensure the frontend is pointed at your backend (default: `NEXT_PUBLIC_DJANGO_API_BASE_URL=http://127.0.0.1:8000` or leave unset).

---

## Quick reference

| What you want              | Command |
|----------------------------|--------|
| Test model only            | `cd webapp && PYTHONPATH=. python risk_scoring/test_risk_service.py` |
| Train model (UCI data)     | `cd webapp && PYTHONPATH=. python risk_scoring/train_from_uci_dataset.py` |
| Run Django API             | `cd webapp && python manage.py runserver` |
| Run frontend               | `cd webapp/frontend && npm run dev` |
| Call risk API (curl)       | `curl -X POST http://127.0.0.1:8000/api/patients/risk-score/ -H "Content-Type: application/json" -d '{"patient_id":"<id>"}'` |
