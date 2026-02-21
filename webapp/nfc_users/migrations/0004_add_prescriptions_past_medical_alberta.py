# Generated manually for new Patient fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nfc_users", "0003_seed_demo_patient"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="current_prescriptions",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="patient",
            name="past_medical_history",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="patient",
            name="use_alberta_health_card",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="patient",
            name="insurance_provider",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AlterField(
            model_name="patient",
            name="insurance_id",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AlterField(
            model_name="patient",
            name="vital_signs",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
