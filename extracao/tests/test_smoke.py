import duckdb


def test_duckdb_runs_query_in_memory() -> None:
    """Confere que o DuckDB abre um banco em memória e responde a uma consulta simples."""
    connection = duckdb.connect(":memory:")
    result = connection.execute("SELECT 1").fetchone()
    assert result == (1,)