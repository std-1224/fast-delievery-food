# Generated by Django 4.2.4 on 2023-11-15 08:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0032_basket"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Basket",
        ),
    ]
