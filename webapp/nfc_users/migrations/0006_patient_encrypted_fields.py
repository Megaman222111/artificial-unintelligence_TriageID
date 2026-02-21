# Add encrypted _ columns, migrate data, remove plain columns

import json
from django.db import migrations, models


def encrypt_patient_data(apps, schema_editor):
    """Copy plain columns to encrypted _ columns then leave plain columns for RemoveField."""
    Patient = apps.get_model("nfc_users", "Patient")
    from nfc_users.encryption import encrypt_value, encrypt_json
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, first_name, last_name, date_of_birth, gender, blood_type, room, "
            "admission_date, primary_diagnosis, insurance_provider, insurance_id, "
            "alberta_health_card_number, emergency_contact, allergies, medications, "
            "current_prescriptions, medical_history, past_medical_history, notes "
            "FROM nfc_users_patient"
        )
        rows = cursor.fetchall()
    cols = [
        "first_name", "last_name", "date_of_birth", "gender", "blood_type", "room",
        "admission_date", "primary_diagnosis", "insurance_provider", "insurance_id",
        "alberta_health_card_number", "emergency_contact", "allergies", "medications",
        "current_prescriptions", "medical_history", "past_medical_history", "notes",
    ]
    for row in rows:
        patient_id = row[0]
        updates = []
        params = []
        for i, col in enumerate(cols):
            val = row[i + 1]
            if val is None:
                val = None
            elif isinstance(val, str) and col in (
                "emergency_contact", "allergies", "medications", "current_prescriptions",
                "medical_history", "past_medical_history", "notes",
            ):
                try:
                    val = json.loads(val) if val.strip() else ({} if col == "emergency_contact" else [])
                except (json.JSONDecodeError, AttributeError):
                    val = {} if col == "emergency_contact" else []
            if col == "emergency_contact":
                enc = encrypt_json(val if isinstance(val, dict) else {}) if val else ""
            elif col in ("allergies", "medications", "current_prescriptions", "medical_history", "past_medical_history", "notes"):
                enc = encrypt_json(val if isinstance(val, list) else []) if val else ""
            else:
                enc = encrypt_value(str(val)) if val else ""
            updates.append(f"_{col} = %s")
            params.append(enc)
        params.append(patient_id)
        with connection.cursor() as c:
            c.execute(
                "UPDATE nfc_users_patient SET " + ", ".join(updates) + " WHERE id = %s",
                params,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("nfc_users", "0005_patient_alberta_health_card_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="_first_name",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_last_name",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_date_of_birth",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_gender",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_blood_type",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_room",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_admission_date",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_primary_diagnosis",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_insurance_provider",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_insurance_id",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_alberta_health_card_number",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_emergency_contact",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_allergies",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_medications",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_current_prescriptions",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_medical_history",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_past_medical_history",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="patient",
            name="_notes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(encrypt_patient_data, migrations.RunPython.noop),
        migrations.RemoveField(model_name="patient", name="first_name"),
        migrations.RemoveField(model_name="patient", name="last_name"),
        migrations.RemoveField(model_name="patient", name="date_of_birth"),
        migrations.RemoveField(model_name="patient", name="gender"),
        migrations.RemoveField(model_name="patient", name="blood_type"),
        migrations.RemoveField(model_name="patient", name="room"),
        migrations.RemoveField(model_name="patient", name="admission_date"),
        migrations.RemoveField(model_name="patient", name="primary_diagnosis"),
        migrations.RemoveField(model_name="patient", name="insurance_provider"),
        migrations.RemoveField(model_name="patient", name="insurance_id"),
        migrations.RemoveField(model_name="patient", name="alberta_health_card_number"),
        migrations.RemoveField(model_name="patient", name="emergency_contact"),
        migrations.RemoveField(model_name="patient", name="allergies"),
        migrations.RemoveField(model_name="patient", name="medications"),
        migrations.RemoveField(model_name="patient", name="current_prescriptions"),
        migrations.RemoveField(model_name="patient", name="medical_history"),
        migrations.RemoveField(model_name="patient", name="past_medical_history"),
        migrations.RemoveField(model_name="patient", name="notes"),
        migrations.RemoveField(model_name="patient", name="vital_signs"),
    ]
