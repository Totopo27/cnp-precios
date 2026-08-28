"""
Motor de Análisis de Estacionalidad de Precios para CNP Precios Costa Rica.
Analiza patrones históricos por mes para identificar épocas de cosecha (precios bajos)
y épocas de escasez (precios altos).
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict


# Nombres de meses en español
NOMBRES_MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"
]


class SeasonalityAnalyzer:
    """
    Calcula la estacionalidad mensual basada en el histórico de precios de un producto.
    """

    def analyze_product_history(self, registros: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Dada una lista de registros [{"fecha": "ISO...", "precio": float}],
        calcula las métricas de estacionalidad por mes.
        """
        if not registros:
            return {}

        precios_por_mes = defaultdict(list)
        for reg in registros:
            try:
                dt = datetime.fromisoformat(reg["fecha"])
                precios_por_mes[dt.month].append(reg["precio"])
            except Exception:
                continue

        if not precios_por_mes:
            return {}

        promedios_mensuales = {}
        for mes_num in range(1, 13):
            if mes_num in precios_por_mes:
                precios = precios_por_mes[mes_num]
                promedios_mensuales[mes_num] = round(sum(precios) / len(precios), 2)

        if not promedios_mensuales:
            return {}

        # Ordenar meses por precio promedio ascendente (primeros = más baratos / cosecha)
        meses_ordenados = sorted(promedios_mensuales.items(), key=lambda x: x[1])

        meses_baratos = [NOMBRES_MESES[m[0]] for m in meses_ordenados[:3]]
        meses_caros = [NOMBRES_MESES[m[0]] for m in meses_ordenados[-3:][::-1]]

        # Evaluar estado del mes actual
        mes_actual = datetime.now().month
        precio_promedio_general = sum(promedios_mensuales.values()) / len(promedios_mensuales)
        precio_mes_actual = promedios_mensuales.get(mes_actual, precio_promedio_general)

        # Clasificación de temporada actual
        ratio = precio_mes_actual / precio_promedio_general
        if ratio <= 0.90:
            estado_actual = "temporada_baja"  # En oferta / Cosecha
        elif ratio >= 1.10:
            estado_actual = "temporada_alta"  # Caro / Escasez
        else:
            estado_actual = "normal"

        return {
            "promedios_mensuales": {NOMBRES_MESES[m]: p for m, p in promedios_mensuales.items()},
            "meses_baratos": meses_baratos,
            "meses_caros": meses_caros,
            "estado_temporada_actual": estado_actual,
            "descuento_estimado_porcentaje": round((1 - ratio) * 100, 1) if ratio < 1.0 else 0.0
        }
