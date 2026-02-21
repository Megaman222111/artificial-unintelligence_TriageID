import json
from datetime import datetime

from django.test import Client, TestCase
from django.utils import timezone

from nfc_users.models import Patient, PatientOutcomeEvent
from risk_scoring.train import _build_training_rows


def _create_patient(
    *,
    patient_id: str,
    nfc_id: str,
    admission_date: str,
    status: str = "active",
) -> Patient:
    p = Patient(
        id=patient_id,
        nfc_id=nfc_id,
        status=status,
        use_alberta_health_card=False,
    )
    p.first_name = "Test"
    p.last_name = "Patient"
    p.date_of_birth = "1980-01-01"
    p.gender = "female"
    p.blood_type = "O+"
    p.room = "A-101"
    p.admission_date = admission_date
    p.primary_diagnosis = "Test diagnosis"
    p.insurance_provider = ""
    p.insurance_id = ""
    p.allergies = []
    p.emergency_contact = {}
    p.medications = ["med-a"]
    p.current_prescriptions = []
    p.medical_history = ["history-a"]
    p.past_medical_history = ["past-a"]
    p.notes = []
    p.save()
    return p


class RiskTrainingLabelTests(TestCase):
    def test_build_training_rows_uses_admission_window(self):
        p_positive = _create_patient(
            patient_id="A-POS",
            nfc_id="A-POS",
            admission_date="2026-01-01",
        )
        p_negative = _create_patient(
            patient_id="B-NEG",
            nfc_id="B-NEG",
            admission_date="2026-01-01",
        )
        _create_patient(
            patient_id="C-PENDING",
            nfc_id="C-PENDING",
            admission_date="2026-03-01",
        )

        PatientOutcomeEvent.objects.create(
            patient=p_positive,
            event_type=PatientOutcomeEvent.EventType.CRITICAL_DETERIORATION,
            event_time=timezone.make_aware(datetime(2026, 1, 20, 12, 0, 0)),
            source="test",
        )
        PatientOutcomeEvent.objects.create(
            patient=p_negative,
            event_type=PatientOutcomeEvent.EventType.CRITICAL_DETERIORATION,
            event_time=timezone.make_aware(datetime(2026, 2, 25, 12, 0, 0)),
            source="test",
        )

        now = timezone.make_aware(datetime(2026, 3, 10, 0, 0, 0))
        rows, labels = _build_training_rows(now=now)

        self.assertEqual(len(rows), 2)
        self.assertEqual(labels, [1, 0])


class RiskApiFlowTests(TestCase):
    def test_nfc_scan_then_risk_score(self):
        patient = _create_patient(
            patient_id="FLOW-001",
            nfc_id="FLOW-001",
            admission_date="2026-02-10",
            status="active",
        )
        client = Client()

        scan_resp = client.post(
            "/api/nfc/scan/",
            data=json.dumps({"tag_id": patient.nfc_id}),
            content_type="application/json",
        )
        self.assertEqual(scan_resp.status_code, 200)
        scan_body = scan_resp.json()
        self.assertEqual(scan_body.get("patient", {}).get("id"), patient.id)

        risk_resp = client.post(
            "/api/patients/risk-score/",
            data=json.dumps({"patient_id": patient.id}),
            content_type="application/json",
        )
        self.assertEqual(risk_resp.status_code, 200)
        risk_body = risk_resp.json()
        self.assertIn(risk_body.get("riskBand"), {"low", "medium", "high"})
        self.assertTrue(0 <= float(risk_body.get("riskProbability", -1)) <= 1)
        self.assertIn(risk_body.get("scoringMode"), {"heuristic", "supervised"})
