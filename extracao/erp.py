import os

import psycopg
from dotenv import load_dotenv


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
