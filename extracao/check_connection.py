"""Confere a conexão com o ERP: mostra o usuário conectado e quantas linhas cada tabela tem.

Como rodar: uv run python -m extracao.check_connection
"""

import psycopg
from psycopg import sql

from extracao.erp import ERP_PRIMARY_KEYS, connect_to_erp


def fetch_current_user(connection: psycopg.Connection) -> str:
    """Devolve o nome do usuário com que a conexão foi aberta."""
    return connection.execute("SELECT current_user").fetchone()[0]


def count_rows(connection: psycopg.Connection, table: str) -> int:
    """Conta as linhas de uma tabela do schema erp_postgresql."""
    query = sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier("erp_postgresql", table))
    return connection.execute(query).fetchone()[0]


def main() -> None:
    """Conecta ao ERP e mostra o usuário e a contagem de cada tabela."""
    with connect_to_erp() as connection:
        print(f"Conectado como: {fetch_current_user(connection)}")
        for table in ERP_PRIMARY_KEYS:
            print(f"erp_postgresql.{table}: {count_rows(connection, table)} linhas")


if __name__ == "__main__":
    main()
