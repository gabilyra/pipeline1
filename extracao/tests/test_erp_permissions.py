"""Testes de integração: conferem no Supabase de verdade que o erp_reader só consegue ler o ERP.

Rodam só no computador da Gabi (precisam do .env). O CI os pula com -m "not integration".

Nenhum teste escreve no banco, por dois motivos:
- os comandos de escrita usam WHERE false, então não afetariam nenhuma linha
  nem se a permissão existisse por engano;
- a conexão nunca confirma nada (commit): tudo é desfeito (rollback) no final de cada teste.
"""

from collections.abc import Iterator

import psycopg
import pytest
from psycopg import sql

from extracao.erp import connect_to_erp

pytestmark = pytest.mark.integration

ERP_TABLES = ["products", "sales", "sale_items"]


@pytest.fixture
def connection() -> Iterator[psycopg.Connection]:
    """Abre uma conexão como erp_reader, entrega ao teste e, no final, desfaz tudo e fecha."""
    connection = connect_to_erp()
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def erp_table(table: str) -> sql.Identifier:
    """Monta o nome completo e protegido de uma tabela do ERP, ex.: "erp_postgresql"."products"."""
    return sql.Identifier("erp_postgresql", table)


def test_connects_as_erp_reader(connection: psycopg.Connection) -> None:
    """A conexão usa o erp_reader, e não o administrador."""
    current_user = connection.execute("SELECT current_user").fetchone()[0]
    assert current_user == "erp_reader"


@pytest.mark.parametrize("table", ERP_TABLES)
def test_can_select_erp_tables(connection: psycopg.Connection, table: str) -> None:
    """O erp_reader consegue consultar as tabelas do ERP."""
    query = sql.SQL("SELECT count(*) FROM {}").format(erp_table(table))
    row_count = connection.execute(query).fetchone()[0]
    assert row_count > 0


@pytest.mark.parametrize("table", ERP_TABLES)
def test_cannot_insert(connection: psycopg.Connection, table: str) -> None:
    """O erp_reader não consegue inserir linhas."""
    query = sql.SQL("INSERT INTO {0} SELECT * FROM {0} WHERE false").format(erp_table(table))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        connection.execute(query)


@pytest.mark.parametrize("table", ERP_TABLES)
def test_cannot_update(connection: psycopg.Connection, table: str) -> None:
    """O erp_reader não consegue alterar linhas."""
    query = sql.SQL("UPDATE {} SET updated_at = updated_at WHERE false").format(erp_table(table))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        connection.execute(query)


@pytest.mark.parametrize("table", ERP_TABLES)
def test_cannot_delete(connection: psycopg.Connection, table: str) -> None:
    """O erp_reader não consegue apagar linhas."""
    query = sql.SQL("DELETE FROM {} WHERE false").format(erp_table(table))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        connection.execute(query)


def test_cannot_see_crm_schema(connection: psycopg.Connection) -> None:
    """O erp_reader não enxerga o crm_api: o CRM só é acessado pela API."""
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        connection.execute("SELECT * FROM crm_api.customers LIMIT 1")
