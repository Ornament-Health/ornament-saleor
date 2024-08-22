# Generated by Django 3.2.23 on 2024-01-19 14:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0181_order_subtotal_as_a_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderline",
            name="is_gift",
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE order_orderline
            ALTER COLUMN is_gift
            SET DEFAULT false;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
