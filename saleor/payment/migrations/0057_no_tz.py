# Generated by Django 3.2.23 on 2024-01-19 08:53

from django.db import migrations

from saleor.utils.migrations import form_alter_timestamp_column_sql


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0056_merge_20231213_0755"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                f"""
            {form_alter_timestamp_column_sql("payment_payment", "created_at")}
            {form_alter_timestamp_column_sql("payment_payment", "modified_at")}
            """
            ],
            reverse_sql=[
                f"""
            {form_alter_timestamp_column_sql("payment_payment", "created_at", True)}
            {form_alter_timestamp_column_sql("payment_payment", "modified_at", True)}
            """
            ],
        ),
        migrations.RunSQL(
            sql=[
                f"""
            {form_alter_timestamp_column_sql("payment_transaction", "created_at")}
            """
            ],
            reverse_sql=[
                f"""
            {form_alter_timestamp_column_sql("payment_transaction", "created_at", True)}
            """
            ],
        ),
        migrations.RunSQL(
            sql=[
                f"""
            {form_alter_timestamp_column_sql("payment_transactionevent", "created_at")}
            """
            ],
            reverse_sql=[
                f"""
            {form_alter_timestamp_column_sql("payment_transactionevent", "created_at", True)}
            """
            ],
        ),
        migrations.RunSQL(
            sql=[
                f"""
            {form_alter_timestamp_column_sql("payment_transactionitem", "created_at")}
            {form_alter_timestamp_column_sql("payment_transactionitem", "modified_at")}
            """
            ],
            reverse_sql=[
                f"""
            {form_alter_timestamp_column_sql("payment_transactionitem", "created_at", True)}
            {form_alter_timestamp_column_sql("payment_transactionitem", "modified_at", True)}
            """
            ],
        ),
    ]
