# Generated by Django 4.1.13 on 2024-07-27 10:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("shipping", "0005_auto_20240620_1333"),
    ]

    operations = [
        migrations.CreateModel(
            name="Postcode",
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
                ("code", models.CharField(max_length=20, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="ShippingZone",
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
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "shipping_price",
                    models.DecimalField(
                        decimal_places=2, help_text="GBP", max_digits=10
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="PostcodeShippingRate",
        ),
        migrations.AddField(
            model_name="postcode",
            name="shipping_zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="postcodes",
                to="shipping.shippingzone",
            ),
        ),
    ]
