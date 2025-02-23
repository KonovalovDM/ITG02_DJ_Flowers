# Generated by Django 5.1.5 on 2025-02-23 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_order_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, default=1000.0, max_digits=10, verbose_name='Цена'),
        ),
    ]
