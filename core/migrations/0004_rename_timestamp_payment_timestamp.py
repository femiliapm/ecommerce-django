# Generated by Django 5.0.4 on 2024-05-03 14:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_payment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payment',
            old_name='Timestamp',
            new_name='timestamp',
        ),
    ]
