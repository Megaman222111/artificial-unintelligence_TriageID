from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nfc_users", "0008_delete_patientoutcomeevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="_important_test_results",
            field=models.TextField(blank=True, default=""),
        ),
    ]
