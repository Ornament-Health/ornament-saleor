# Generated by Django 3.2.23 on 2024-01-18 14:11

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0182_merge_20240110_1408'),
    ]

    operations = [
        migrations.AddField(
            model_name='fulfillment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='orderevent',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='orderevent',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='orderline',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
