"""Testes da gravação na bronze. Não usam o Supabase: rodam no CI."""

import pytest

from extracao.bronze import to_duckdb_type


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
