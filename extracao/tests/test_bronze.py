"""Testes da gravação na bronze. Não usam o Supabase: rodam no CI.

O DuckDB roda em memória, criado e descartado em cada teste.
As datas com fuso (TIMESTAMPTZ) são conferidas dentro do SQL: devolvê-las
ao Python exigiria a biblioteca pytz, que o pipeline não usa.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import duckdb
import pytest

from extracao.bronze import to_duckdb_type, write_table

# Uma tabela pequena, no formato que o fetch_columns e o fetch_rows devolvem.
COLUMNS = [
    ("product_id", "integer", 32, 0),
    ("product_name", "text", None, None),
    ("unit_price", "numeric", 10, 2),
    ("created_at", "timestamp with time zone", None, None),
]
CREATED_AT = datetime(2025, 1, 8, tzinfo=UTC)
# Com sujeira de propósito: espaços sobrando e maiúsculas misturadas. A bronze guarda igual.
ROWS = [
    (1, "  Sérum Facial  ", Decimal("149.90"), CREATED_AT),
    (2, "MÁSCARA de argila", Decimal("59.00"), CREATED_AT),
]
EXTRACTED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


@pytest.fixture
def connection() -> Iterator[duckdb.DuckDBPyConnection]:
    """Abre um DuckDB em memória, que some ao final do teste."""
    connection = duckdb.connect(":memory:")
    try:
        yield connection
    finally:
        connection.close()


def count_rows(connection: duckdb.DuckDBPyConnection) -> int:
    """Conta as linhas de bronze.erp_products."""
    return connection.execute("SELECT count(*) FROM bronze.erp_products").fetchone()[0]


@pytest.mark.parametrize(
    ("data_type", "precision", "scale", "expected"),
    [
        ("integer", 32, 0, "INTEGER"),
        ("text", None, None, "VARCHAR"),
        ("date", None, None, "DATE"),
        ("timestamp with time zone", None, None, "TIMESTAMPTZ"),
        ("numeric", 10, 2, "DECIMAL(10, 2)"),
        ("numeric", 4, 2, "DECIMAL(4, 2)"),
    ],
)
def test_to_duckdb_type_translates_known_types(
    data_type: str, precision: int | None, scale: int | None, expected: str
) -> None:
    """Cada tipo do ERP vira o equivalente no DuckDB, e o numeric mantém precisão e escala."""
    assert to_duckdb_type(data_type, precision, scale) == expected


def test_to_duckdb_type_fails_for_unknown_type() -> None:
    """Um tipo que o pipeline não conhece faz a função parar com uma mensagem clara."""
    with pytest.raises(ValueError, match="sem equivalente"):
        to_duckdb_type("xml", None, None)


def test_to_duckdb_type_fails_for_numeric_without_precision() -> None:
    """Um numeric sem precisão não tem um DECIMAL equivalente seguro."""
    with pytest.raises(ValueError, match="sem precisão"):
        to_duckdb_type("numeric", None, None)


def test_write_table_keeps_source_columns_and_adds_extracted_at(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """Mesmas colunas da origem, na mesma ordem, com os tipos traduzidos, e _extracted_at por último."""
    write_table(connection, "erp_products", COLUMNS, ROWS, EXTRACTED_AT)
    columns = connection.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'bronze' AND table_name = 'erp_products'
        ORDER BY ordinal_position
        """
    ).fetchall()
    assert columns == [
        ("product_id", "INTEGER"),
        ("product_name", "VARCHAR"),
        ("unit_price", "DECIMAL(10,2)"),
        ("created_at", "TIMESTAMP WITH TIME ZONE"),
        ("_extracted_at", "TIMESTAMP WITH TIME ZONE"),
    ]


def test_write_table_keeps_values_exactly_as_source(connection: duckdb.DuckDBPyConnection) -> None:
    """Os valores chegam iguais, inclusive a sujeira e os centavos exatos."""
    write_table(connection, "erp_products", COLUMNS, ROWS, EXTRACTED_AT)
    rows = connection.execute(
        "SELECT product_id, product_name, unit_price FROM bronze.erp_products ORDER BY product_id"
    ).fetchall()
    assert rows == [
        (1, "  Sérum Facial  ", Decimal("149.90")),
        (2, "MÁSCARA de argila", Decimal("59.00")),
    ]


def test_write_table_keeps_timestamps_and_fills_extracted_at(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """As datas da origem chegam iguais, e toda linha recebe o momento da extração."""
    write_table(connection, "erp_products", COLUMNS, ROWS, EXTRACTED_AT)
    matching_rows = connection.execute(
        "SELECT count(*) FROM bronze.erp_products WHERE created_at = ? AND _extracted_at = ?",
        [CREATED_AT, EXTRACTED_AT],
    ).fetchone()[0]
    assert matching_rows == len(ROWS)


def test_write_table_twice_does_not_duplicate(connection: duckdb.DuckDBPyConnection) -> None:
    """Gravar duas vezes substitui a tabela: as linhas não se repetem."""
    write_table(connection, "erp_products", COLUMNS, ROWS, EXTRACTED_AT)
    write_table(connection, "erp_products", COLUMNS, ROWS, EXTRACTED_AT)
    assert count_rows(connection) == len(ROWS)


def test_write_table_failure_keeps_previous_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Se a gravação falha no meio, a tabela antiga continua intacta."""
    write_table(connection, "erp_products", COLUMNS, ROWS, EXTRACTED_AT)
    broken_rows = [(3, "Linha com colunas faltando")]
    with pytest.raises(duckdb.Error):
        write_table(connection, "erp_products", COLUMNS, broken_rows, EXTRACTED_AT)
    assert count_rows(connection) == len(ROWS)


def test_write_table_without_rows_creates_empty_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Sem linhas, a tabela é criada vazia, com a estrutura certa."""
    write_table(connection, "erp_products", COLUMNS, [], EXTRACTED_AT)
    assert count_rows(connection) == 0
