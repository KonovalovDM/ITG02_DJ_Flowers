# Generated by Django 5.1.5 on 2025-02-09 09:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_user_is_admin_alter_product_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='telegram_username',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='Telegram Username'),
        ),
    ]
