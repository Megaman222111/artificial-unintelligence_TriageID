from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("nfc_users", "0006_patient_encrypted_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatientOutcomeEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("critical_deterioration", "Critical Deterioration"),
                            ("death", "Death"),
                        ],
                        max_length=64,
                    ),
                ),
                ("event_time", models.DateTimeField()),
                ("source", models.CharField(default="manual", max_length=64)),
                ("note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outcome_events",
                        to="nfc_users.patient",
                    ),
                ),
            ],
            options={
                "ordering": ["-event_time", "-created_at"],
            },
        ),
    ]

