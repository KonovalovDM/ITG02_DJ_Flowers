# Generated by Django 5.1.5 on 2025-02-23 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_user_delivery_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Адрес доставки'),
        ),
    ]
