# Generated by Django 5.1.7 on 2025-06-04 05:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_userprofile_date_of_birth"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="email_verified",
            field=models.BooleanField(default=False, verbose_name="E-posta Doğrulandı"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="phone_number_verified",
            field=models.BooleanField(
                default=False, verbose_name="Telefon Numarası Doğrulandı"
            ),
        ),
    ]
