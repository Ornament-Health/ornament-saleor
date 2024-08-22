# Generated by Django 3.2.23 on 2024-05-08 09:24

import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("product", "0186_alter_productmedia_alt"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="productvariantchannellisting",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["price_amount", "channel_id"],
                name="product_pro_price_a_fb6bd3_gin",
            ),
        ),
    ]
