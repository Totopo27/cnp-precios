"""
Pruebas unitarias para el motor ETL y utilidades de CNP Precios.
"""
from datetime import datetime
from pathlib import Path
import json
import pytest

from src.core.utils import slugify_product_name, calculate_trend
from src.etl.parser import CNPParser
from src.etl.publisher import DataPublisher


def test_slugify_product_name():
    assert slugify_product_name("Aguacate Hass Nacional") == "Aguacate_hass_nacional"
    assert slugify_product_name(" Tomate primera ") == "Tomate_primera"
    assert slugify_product_name("Brócoli") == "Brócoli"


def test_calculate_trend():
    pct, tipo = calculate_trend(500.0, 450.0)
    assert tipo == "subida"
    assert pct == 11.1

    pct, tipo = calculate_trend(400.0, 450.0)
    assert tipo == "bajada"
    assert pct == -11.1

    pct, tipo = calculate_trend(500.0, 495.0)
    assert tipo == "estable"


def test_clean_price():
    parser = CNPParser()
    assert parser.clean_price("¢1,200.00") == 1200.0
    assert parser.clean_price("500") == 500.0
    assert parser.clean_price("1.500,50") == 1500.5
    assert parser.clean_price("N/A") is None


def test_data_publisher(tmp_path):
    historicos_dir = tmp_path / "historicos"
    publisher = DataPublisher(data_dir=tmp_path, historicos_dir=historicos_dir)

    # Insertar registros
    fecha_1 = datetime(2026, 8, 20)
    fecha_2 = datetime(2026, 8, 27)

    filepath = publisher.update_product_history(
        "Tomate prueba",
        [(fecha_1, 500.0), (fecha_2, 550.0)]
    )

    assert filepath.exists()
    with open(filepath, "r", encoding="utf-8") as f:
        content = json.load(f)
        assert len(content) == 2
        assert content[0]["precio"] == 500.0
        assert content[1]["precio"] == 550.0

    # Recalcular resúmenes
    res = publisher.rebuild_all_summaries()
    assert res["total_productos"] == 1
    assert res["total_registros"] == 2
