"""Extrai as 3 tabelas do ERP e grava na camada bronze do DuckDB.

Como rodar: uv run python -m extracao.extract_erp

Atenção: substitui as tabelas bronze.erp_* que já existirem no arquivo do DuckDB.
"""

from datetime import UTC, datetime

from dotenv import load_dotenv

from extracao.bronze import connect_to_duckdb, count_bronze_rows, write_table
from extracao.erp import ERP_PRIMARY_KEYS, connect_to_erp, fetch_columns, fetch_rows, get_env


def main() -> None:
    """Lê primeiro as 3 tabelas do ERP inteiras e só depois grava cada uma na bronze."""
    load_dotenv()
    extracted_at = datetime.now(UTC)

    source_tables = {}
    with connect_to_erp() as erp_connection:
        for table in ERP_PRIMARY_KEYS:
            source_tables[table] = (fetch_columns(erp_connection, table), fetch_rows(erp_connection, table))

    with connect_to_duckdb(get_env("DUCKDB_PATH")) as duckdb_connection:
        for table, (columns, rows) in source_tables.items():
            bronze_table = f"erp_{table}"
            write_table(duckdb_connection, bronze_table, columns, rows, extracted_at)
            print(f"bronze.{bronze_table}: {count_bronze_rows(duckdb_connection, bronze_table)} linhas")


if __name__ == "__main__":
    main()
