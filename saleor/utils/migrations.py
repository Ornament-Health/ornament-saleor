def form_alter_timestamp_column_sql(
    table: str, column: str, reverse: bool = False
) -> str:
    tz = "with" if reverse else "without"
    return f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMP {tz} time zone;"
