# Generated by Django 4.1.13 on 2024-10-28 11:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0015_device_delete_apikey"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="firebase_token",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
