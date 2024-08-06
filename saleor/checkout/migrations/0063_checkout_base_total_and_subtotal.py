# Generated by Django 3.2.23 on 2024-01-03 08:53

from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "checkout",
            "0063_no_tz",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="checkout",
            name="base_subtotal_amount",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="checkout",
            name="base_total_amount",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.RunSQL(
            """
            ALTER TABLE checkout_checkout
            ALTER COLUMN base_subtotal_amount
            SET DEFAULT 0;
            """,
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            """
            ALTER TABLE checkout_checkout
            ALTER COLUMN base_total_amount
            SET DEFAULT 0;
            """,
            migrations.RunSQL.noop,
        ),
    ]
