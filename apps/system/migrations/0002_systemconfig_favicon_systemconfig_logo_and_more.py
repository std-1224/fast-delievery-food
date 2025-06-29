# Generated by Django 4.2.4 on 2023-10-18 03:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemconfig",
            name="favicon",
            field=models.ImageField(
                blank=True,
                max_length=255,
                null=True,
                upload_to="image",
                verbose_name="Favicon",
            ),
        ),
        migrations.AddField(
            model_name="systemconfig",
            name="logo",
            field=models.ImageField(
                blank=True,
                max_length=255,
                null=True,
                upload_to="image",
                verbose_name="Logo",
            ),
        ),
        migrations.AddField(
            model_name="systemconfig",
            name="site_name",
            field=models.CharField(
                default="KM", max_length=100, verbose_name="Currency"
            ),
        ),
    ]
