# Generated by Django 3.2.25 on 2024-09-09 13:38

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('attribute', '0048_no_tz'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignedproductattributevalue',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='assignedproductattributevalue',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]