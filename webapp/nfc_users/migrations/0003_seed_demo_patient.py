# Data migration: one demo patient for React frontend / NFC scan

from django.db import migrations


def create_demo_patient(apps, schema_editor):
    Patient = apps.get_model("nfc_users", "Patient")
    if Patient.objects.filter(nfc_id="PROD-USER-001").exists():
        return
    Patient.objects.create(
        id="PROD-USER-001",
        first_name="Avery",
        last_name="Brooks",
        date_of_birth="1992-04-14",
        gender="Female",
        blood_type="O+",
        nfc_id="PROD-USER-001",
        status="active",
        room="ICU-204",
        admission_date="2026-02-10",
        allergies=["Penicillin"],
        primary_diagnosis="Acute Myocardial Infarction",
        insurance_provider="BlueCross BlueShield",
        insurance_id="BCB-449281",
        emergency_contact={
            "name": "Jordan Brooks",
            "relationship": "Spouse",
            "phone": "(555) 123-4567",
        },
        medications=[
            {"name": "Aspirin", "dosage": "81mg", "frequency": "Daily"},
            {"name": "Metoprolol", "dosage": "50mg", "frequency": "Twice daily"},
        ],
        vital_signs={
            "heartRate": 78,
            "bloodPressure": "128/82",
            "temperature": 98.6,
            "oxygenSaturation": 97,
        },
        medical_history=[
            "Hypertension (diagnosed 2018)",
            "Type 2 Diabetes (diagnosed 2020)",
        ],
        notes=["Demo patient for NFC scan"],
    )


def reverse(apps, schema_editor):
    Patient = apps.get_model("nfc_users", "Patient")
    Patient.objects.filter(id="PROD-USER-001").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("nfc_users", "0002_add_patient"),
    ]

    operations = [
        migrations.RunPython(create_demo_patient, reverse),
    ]
