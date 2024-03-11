# Generated by Django 3.2.23 on 2024-01-19 08:29

from django.db import migrations

from saleor.utils.migrations import form_alter_timestamp_column_sql


class Migration(migrations.Migration):
    dependencies = [
        ("invoice", "0009_alter_invoice_options"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                f"""
            {form_alter_timestamp_column_sql("invoice_invoice", "created_at")}
            {form_alter_timestamp_column_sql("invoice_invoice", "updated_at")}
            {form_alter_timestamp_column_sql("invoice_invoice", "created")}
            """
            ],
            reverse_sql=[
                f"""
            {form_alter_timestamp_column_sql("invoice_invoice", "created_at", True)}
            {form_alter_timestamp_column_sql("invoice_invoice", "updated_at", True)}
            {form_alter_timestamp_column_sql("invoice_invoice", "created", True)}
            """
            ],
        ),
        migrations.RunSQL(
            sql=[
                f"""
            {form_alter_timestamp_column_sql("invoice_invoiceevent", "date")}
            """
            ],
            reverse_sql=[
                f"""
            {form_alter_timestamp_column_sql("invoice_invoiceevent", "date", True)}
            """
            ],
        ),
    ]