"""
Pruebas unitarias para el servicio de bot de Telegram.
"""
import pytest
from src.bot.services import BotQueryService


def test_bot_query_service():
    service = BotQueryService()
    
    # 1. Consulta de producto existente (ejemplo: Aguacate)
    resp = service.query_product("aguacate")
    assert "Aguacate" in resp
    assert "Precio Actual" in resp
    assert "Tendencia" in resp

    # 2. Consulta con typo ortográfico
    resp_typo = service.query_product("tomat")
    assert "Tomate" in resp_typo

    # 3. Consulta de temporada
    resp_temp = service.get_seasonal_recommendations()
    assert len(resp_temp) > 0

    # 4. Consulta de tendencias
    resp_trend = service.get_trends_summary()
    assert "Resumen Semanal" in resp_trend
