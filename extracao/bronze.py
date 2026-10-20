"""Gravação na camada bronze do DuckDB."""

from datetime import datetime

import duckdb

# Tipos do PostgreSQL (como aparecem no information_schema) e o equivalente no DuckDB.
# O numeric fica de fora porque depende da precisão e da escala: é tratado à parte.
POSTGRES_TO_DUCKDB_TYPES = {
    "integer": "INTEGER",
    "text": "VARCHAR",
    "date": "DATE",
    "timestamp with time zone": "TIMESTAMPTZ",
}


def to_duckdb_type(data_type: str, precision: int | None, scale: int | None) -> str:
    """Traduz um tipo do PostgreSQL para o tipo equivalente no DuckDB.

    Para tipos que o pipeline ainda não conhece, para com um erro claro,
    em vez de guardar o dado de um jeito errado.
    """
    if data_type == "numeric":
        if precision is None:
            raise ValueError("Coluna numeric sem precisão definida: o DuckDB precisa saber quantos dígitos guardar.")
        return f"DECIMAL({precision}, {scale})"
    if data_type not in POSTGRES_TO_DUCKDB_TYPES:
        raise ValueError(f"Tipo do PostgreSQL sem equivalente definido no pipeline: {data_type}")
    return POSTGRES_TO_DUCKDB_TYPES[data_type]


def quote_identifier(name: str) -> str:
    """Põe um nome de coluna ou tabela entre aspas duplas, para o DuckDB lê-lo como nome, e não como SQL."""
    escaped_name = name.replace('"', '""')
    return f'"{escaped_name}"'


def write_table(
    connection: duckdb.DuckDBPyConnection,
    bronze_table: str,
    columns: list[tuple[str, str, int | None, int | None]],
    rows: list[tuple],
    extracted_at: datetime,
) -> None:
    """Grava uma tabela no schema bronze, substituindo a anterior, com a coluna _extracted_at a mais.

    Tudo acontece numa única transação: se algo falhar no meio,
    a tabela antiga volta exatamente como estava.
    """
    column_definitions = [
        f"{quote_identifier(name)} {to_duckdb_type(data_type, precision, scale)}"
        for name, data_type, precision, scale in columns
    ]
    column_definitions.append(f"{quote_identifier('_extracted_at')} TIMESTAMPTZ")
    table_name = f"bronze.{quote_identifier(bronze_table)}"
    placeholders = ", ".join("?" for _ in column_definitions)

    connection.begin()
    try:
        connection.execute("CREATE SCHEMA IF NOT EXISTS bronze")
        connection.execute(f"CREATE OR REPLACE TABLE {table_name} ({', '.join(column_definitions)})")
        if rows:
            connection.executemany(
                f"INSERT INTO {table_name} VALUES ({placeholders})",
                [row + (extracted_at,) for row in rows],
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
