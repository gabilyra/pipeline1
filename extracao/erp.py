import os

import psycopg
from dotenv import load_dotenv
from psycopg import sql

# Chave primária de cada tabela do ERP: as linhas são lidas sempre nessa ordem.
ERP_PRIMARY_KEYS = {
    "products": "product_id",
    "sales": "sale_id",
    "sale_items": "sale_item_id",
}


def get_env(name: str) -> str:
    """Lê uma variável de ambiente e para com uma mensagem clara se ela estiver faltando ou vazia."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"A variável {name} não está definida. Confira o arquivo .env.")
    return value


def connect_to_erp() -> psycopg.Connection:
    """Abre uma conexão com o ERP no Supabase, com o usuário erp_reader e conexão criptografada."""
    load_dotenv()
    return psycopg.connect(
        host=get_env("ERP_DB_HOST"),
        port=get_env("ERP_DB_PORT"),
        dbname=get_env("ERP_DB_NAME"),
        user=get_env("ERP_DB_USER"),
        password=get_env("ERP_DB_PASSWORD"),
        sslmode="require",
    )


def fetch_columns(
    connection: psycopg.Connection, table: str
) -> list[tuple[str, str, int | None, int | None]]:
    """Lê no catálogo do PostgreSQL as colunas de uma tabela do ERP, na ordem da origem.

    Cada coluna vem como (nome, tipo, precisão, escala). Precisão e escala só existem
    para números (ex.: numeric(10, 2)); nos outros tipos, vêm como None.
    """
    query = """
        SELECT column_name, data_type, numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_schema = 'erp_postgresql'
          AND table_name = %s
        ORDER BY ordinal_position
    """
    columns = connection.execute(query, (table,)).fetchall()
    if not columns:
        raise RuntimeError(
            f"Nenhuma coluna encontrada para erp_postgresql.{table}. "
            "Confira o nome da tabela e se o script sql/erp_reader.sql foi rodado após a última recarga da base."
        )
    return columns


def fetch_rows(connection: psycopg.Connection, table: str) -> list[tuple]:
    """Lê todas as linhas de uma tabela do ERP, ordenadas pela chave primária.

    As colunas vêm na ordem da origem, a mesma devolvida por fetch_columns.
    """
    query = sql.SQL("SELECT * FROM {table} ORDER BY {primary_key}").format(
        table=sql.Identifier("erp_postgresql", table),
        primary_key=sql.Identifier(ERP_PRIMARY_KEYS[table]),
    )
    return connection.execute(query).fetchall()
