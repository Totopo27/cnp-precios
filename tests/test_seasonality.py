"""
Pruebas unitarias para el motor de estacionalidad y resolución de alias.
"""
from datetime import datetime
import pytest

from src.core.seasonality import SeasonalityAnalyzer
from src.core.alias_matcher import ProductAliasMatcher


def test_seasonality_analyzer():
    analyzer = SeasonalityAnalyzer()

    # Generar registros mock de 12 meses
    registros = []
    for mes in range(1, 13):
        # Enero a Marzo baratos (500), Julio a Setiembre caros (1000)
        precio = 500.0 if mes in [1, 2, 3] else (1000.0 if mes in [7, 8, 9] else 750.0)
        registros.append({
            "fecha": datetime(2025, mes, 15).isoformat(),
            "precio": precio
        })

    res = analyzer.analyze_product_history(registros)

    assert "meses_baratos" in res
    assert "meses_caros" in res
    assert len(res["meses_baratos"]) == 3
    assert "Enero" in res["meses_baratos"]
    assert "Julio" in res["meses_caros"]


def test_product_alias_matcher():
    productos = [
        "Aguacate criollo",
        "Aguacate hass",
        "Aguacate hass nacional",
        "Tomate primera",
        "Papa blanca"
    ]
    matcher = ProductAliasMatcher(productos)

    # 1. Búsqueda por subcadena / alias
    matches = matcher.search("tomate")
    assert len(matches) > 0
    assert matches[0][0] == "Tomate primera"

    # 2. Errores ortográficos / typos (fuzzy match)
    matches_fuzzy = matcher.search("aguacate crilo")
    assert len(matches_fuzzy) > 0
    assert matches_fuzzy[0][0] == "Aguacate criollo"

    best = matcher.get_best_match("papas blancas")
    assert best == "Papa blanca"
