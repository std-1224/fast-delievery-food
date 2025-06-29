# Generated by Django 4.1.13 on 2025-06-21 18:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shipping", "0006_postcode_shippingzone_delete_postcodeshippingrate_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="postcode",
            name="code",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="shippingzone",
            name="name",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="shippingzone",
            name="shipping_price",
            field=models.DecimalField(
                decimal_places=100, help_text="GBP", max_digits=255
            ),
        ),
    ]
