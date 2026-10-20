"""Testes de integração: conferem a busca no ERP de verdade (precisam do .env)."""

from collections.abc import Iterator

import psycopg
import pytest

from extracao.erp import connect_to_erp, fetch_columns

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
