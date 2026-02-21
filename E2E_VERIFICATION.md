# End-to-end verification: NFC → Backend → Risk model → Frontend

This doc summarizes how the full flow is wired and what was verified.

## Flow

1. **NFC scan**
   - User connects Arduino reader (Web Serial), taps wristband.
   - `nfc-scan-view.tsx` → `handleTagReadFromSerial(tagId)` → `scanNfcTag(tagId)`.
   - **POST** `http://127.0.0.1:8000/api/nfc/scan/` with `{ "tag_id": "<tagId>" }`.
   - Backend `nfc_scan` in `nfc_users/views.py` does `Patient.objects.get(nfc_id=tag_id)`, returns `{ "patient": p.to_api_dict() }`.
   - Frontend sets `scannedPatient` and renders `<PatientOverlay patient={scannedPatient} />`.

2. **Risk score (overlay)**
   - `PatientOverlay` has `useEffect` on `patient.id` that calls `getPatientRiskScore(patient.id)`.
   - **POST** `/api/patients/risk-score/` with `{ "patient_id": patient.id }`.
   - Backend `patient_risk_score` gets `Patient.objects.get(pk=patient_id)`, calls `RISK_SERVICE.predict(patient)`.
   - `RiskScoringService` uses `patient_to_feature_dict(patient)` (reads Patient’s encrypted props), loads latest `risk_model_*.joblib` from `risk_scoring/artifacts/`, runs pipeline, returns `risk_band` (low/medium/high), `risk_probability`, `top_factors`, etc.
   - Frontend displays badge (low/medium/high), probability, and top factors.

3. **Risk score (detail page)**
   - From dashboard list or overlay “View full profile”, user goes to `/dashboard/patient/[id]`.
   - Page fetches patient via `getPatientById(id)` then renders `<PatientDetail patient={patient} />`.
   - `PatientDetail` calls `getPatientRiskScore(patient.id)` and shows the same risk block.

## Verified

- **URLs**: `config/urls.py` includes `api/nfc/scan/` and `api/patients/` (patient_urls); `patient_urls.py` has `risk-score/` → `patient_risk_score`.
- **Views**: `nfc_scan` returns patient by `nfc_id`; `patient_risk_score` loads patient by `pk`, calls `RISK_SERVICE.predict(patient)`, returns JSON matching `PatientRiskScore`.
- **Features**: `patient_to_feature_dict` uses only attributes present on `Patient` (date_of_birth, admission_date, allergies, medications, status, primary_diagnosis, etc.); `Patient.to_api_dict()` includes `id` so frontend has `patient.id`.
- **Frontend**: `scanNfcTag` returns `result.patient`; overlay and detail both call `getPatientRiskScore(patient.id)` and render risk band + probability + factors; `API_BASE_URL` defaults to `http://127.0.0.1:8000`.
- **CORS**: `config/settings.py` has `corsheaders` and `CORS_ALLOW_ALL_ORIGINS = DEBUG` so Next.js on another port can call the API.
- **Model**: Standalone test `risk_scoring/test_risk_service.py` loads artifact and returns valid `risk_band` and probability (run: `cd webapp && PYTHONPATH=. python risk_scoring/test_risk_service.py`).

## How to run E2E manually

1. **Backend**: `cd webapp && python manage.py runserver`
2. **Frontend**: `cd webapp/frontend && npm run dev`
3. Open app, connect NFC reader, scan a wristband linked to a patient → overlay should show patient and risk (low/medium/high).
4. Or open a patient from the dashboard → detail page should show the same risk block.
