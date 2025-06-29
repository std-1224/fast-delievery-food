# Generated by Django 4.1.13 on 2025-06-06 19:44

from django.db import migrations, models
import oscar.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0019_alter_shippingaddress_postcode"),
    ]

    operations = [
        migrations.AlterField(
            model_name="billingaddress",
            name="postcode",
            field=oscar.models.fields.UppercaseCharField(
                blank=True, max_length=255, verbose_name="Post/Zip-code"
            ),
        ),
        migrations.AlterField(
            model_name="shippingaddress",
            name="postcode",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Postcode"
            ),
        ),
    ]
