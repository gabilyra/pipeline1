"""Testes de integração: conferem a busca no ERP de verdade (precisam do .env)."""

from collections.abc import Iterator

import psycopg
import pytest

from extracao.erp import connect_to_erp, fetch_columns, fetch_rows

pytestmark = pytest.mark.integration


@pytest.fixture
def connection() -> Iterator[psycopg.Connection]:
    """Abre uma conexão como erp_reader, entrega ao teste e, no final, desfaz tudo e fecha."""
    connection = connect_to_erp()
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def test_fetch_columns_returns_products_columns_in_order(connection: psycopg.Connection) -> None:
    """As colunas de products vêm na ordem da origem, com tipo, precisão e escala."""
    columns = fetch_columns(connection, "products")
    assert columns == [
        ("product_id", "integer", 32, 0),
        ("product_name", "text", None, None),
        ("category", "text", None, None),
        ("unit_price", "numeric", 10, 2),
        ("unit_cost", "numeric", 10, 2),
        ("created_at", "timestamp with time zone", None, None),
        ("updated_at", "timestamp with time zone", None, None),
    ]


def test_fetch_columns_fails_for_unknown_table(connection: psycopg.Connection) -> None:
    """Uma tabela que não existe faz a função parar com uma mensagem clara."""
    with pytest.raises(RuntimeError, match="Nenhuma coluna encontrada"):
        fetch_columns(connection, "tabela_que_nao_existe")


@pytest.mark.parametrize(
    ("table", "expected_rows"),
    [("products", 23), ("sales", 3764), ("sale_items", 6195)],
)
def test_fetch_rows_returns_all_rows(
    connection: psycopg.Connection, table: str, expected_rows: int
) -> None:
    """A busca real traz o volume da seção 5.3 do PRD."""
    rows = fetch_rows(connection, table)
    assert len(rows) == expected_rows


@pytest.mark.parametrize("table", ["products", "sales", "sale_items"])
def test_fetch_rows_matches_columns_and_order(connection: psycopg.Connection, table: str) -> None:
    """Cada linha tem uma posição por coluna, e as linhas vêm em ordem crescente de chave primária."""
    columns = fetch_columns(connection, table)
    rows = fetch_rows(connection, table)
    assert all(len(row) == len(columns) for row in rows)
    primary_keys = [row[0] for row in rows]
    assert primary_keys == sorted(primary_keys)
