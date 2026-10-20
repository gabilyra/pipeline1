"""Gravação na camada bronze do DuckDB."""

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
