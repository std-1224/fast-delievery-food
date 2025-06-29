# Generated by Django 4.2.4 on 2023-11-03 08:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0008_alter_menu_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="Slider",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(default="", max_length=100)),
                ("name", models.CharField(default="", max_length=100)),
                ("content", models.CharField(default="", max_length=100)),
                ("button_label", models.CharField(max_length=50)),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        max_length=255,
                        null=True,
                        upload_to="image",
                        verbose_name="Image",
                    ),
                ),
            ],
        ),
    ]
