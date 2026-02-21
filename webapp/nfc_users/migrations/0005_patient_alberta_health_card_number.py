# Add Alberta Health Card number field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nfc_users", "0004_add_prescriptions_past_medical_alberta"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="alberta_health_card_number",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
