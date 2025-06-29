# Generated by Django 4.2.4 on 2024-03-09 03:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0010_systemconfig_display_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemconfig",
            name="home_page_background_image",
            field=models.ImageField(
                blank=True,
                max_length=255,
                null=True,
                upload_to="image",
                verbose_name="Home page background image",
            ),
        ),
        migrations.AddField(
            model_name="systemconfig",
            name="home_page_layout",
            field=models.CharField(
                choices=[("Slider", "Slider"), ("BackgroundTop", "BackgroundTop")],
                default="Slider",
                max_length=100,
            ),
        ),
    ]
