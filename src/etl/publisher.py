"""
Modulo de actualización y publicación de datos JSON para el dashboard web (docs/data).
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from src.config import (
    DATA_DIR,
    HISTORICOS_DIR,
    PRODUCTOS_JSON,
    RESUMEN_JSON,
    HISTORICOS_INDEX_JSON,
    ESTACIONALIDAD_JSON
)
from src.core.utils import slugify_product_name, calculate_trend
from src.core.seasonality import SeasonalityAnalyzer

class DataPublisher:
    """
    Gestiona la actualización atómica y persistencia de datos históricos,
    resúmenes por producto, estacionalidad y métricas globales.
    """

    def __init__(self, data_dir: Path = DATA_DIR, historicos_dir: Path = HISTORICOS_DIR):
        self.data_dir = data_dir
        self.historicos_dir = historicos_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.historicos_dir.mkdir(parents=True, exist_ok=True)
        self.seasonality_analyzer = SeasonalityAnalyzer()

        self.productos_json = self.data_dir / "productos.json"
        self.resumen_json = self.data_dir / "resumen.json"
        self.historicos_index_json = self.data_dir / "historicos_index.json"
        self.estacionalidad_json = self.data_dir / "estacionalidad.json"

    def update_product_history(self, nombre_producto: str, nuevos_registros: List[Tuple[datetime, float]]) -> Path:
        """
        Fusiona nuevos registros con el historial existente de un producto sin duplicados.
        Retorna la ruta del archivo histórico actualizado.
        """
        slug = slugify_product_name(nombre_producto)
        filepath = self.historicos_dir / f"{slug}.json"
        
        registros_existentes = {}
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        # Parse ISO datetime
                        dt = datetime.fromisoformat(item["fecha"])
                        registros_existentes[dt.isoformat()] = item["precio"]
            except Exception as e:
                print(f"[Warning] Error leyendo historial existente de {slug}: {e}")

        # Agregar o actualizar con los nuevos registros
        for fecha, precio in nuevos_registros:
            iso_key = fecha.isoformat()
            registros_existentes[iso_key] = round(float(precio), 2)

        # Ordenar cronológicamente
        registros_ordenados = [
            {"fecha": iso_str, "precio": precio}
            for iso_str, precio in sorted(registros_existentes.items(), key=lambda x: x[0])
        ]

        # Guardar archivo histórico
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(registros_ordenados, f, ensure_ascii=False, indent=2)

        return filepath

    def rebuild_all_summaries(self) -> dict:
        """
        Recorre todos los archivos en historicos_dir/*.json, recalcula
        productos.json, resumen.json, estacionalidad.json e historicos_index.json.
        """
        archivos_historicos = list(self.historicos_dir.glob("*.json"))
        productos_resumen = []
        estacionalidad_global = {}
        
        total_registros_global = 0
        todos_los_precios = []
        fechas_globales = []

        index_historicos = {}

        for filepath in archivos_historicos:
            with open(filepath, "r", encoding="utf-8") as f:
                registros = json.load(f)
            
            if not registros:
                continue

            total_registros_global += len(registros)
            
            # Nombre legible a partir del slug
            slug = filepath.stem
            nombre_legible = slug.replace("_", " ")

            precios = [r["precio"] for r in registros]
            fechas = [datetime.fromisoformat(r["fecha"]) for r in registros]

            todos_los_precios.extend(precios)
            fechas_globales.extend(fechas)

            precio_actual = precios[-1]
            precio_anterior = precios[-2] if len(precios) > 1 else precio_actual
            precio_promedio = round(sum(precios) / len(precios), 2)
            precio_minimo = round(min(precios), 2)
            precio_maximo = round(max(precios), 2)
            ultima_fecha = max(fechas)

            pct_trend, tipo_trend = calculate_trend(precio_actual, precio_anterior)
            
            # Análisis de estacionalidad
            seasonality = self.seasonality_analyzer.analyze_product_history(registros)
            if seasonality:
                estacionalidad_global[nombre_legible] = seasonality

            prod_data = {
                "nombre": nombre_legible,
                "precio_actual": precio_actual,
                "precio_promedio": precio_promedio,
                "precio_minimo": precio_minimo,
                "precio_maximo": precio_maximo,
                "total_registros": len(registros),
                "ultima_fecha": ultima_fecha.isoformat(),
                "tendencia_porcentaje": pct_trend,
                "tendencia_tipo": tipo_trend,
                "estado_temporada": seasonality.get("estado_temporada_actual", "normal") if seasonality else "normal",
                "meses_baratos": seasonality.get("meses_baratos", []) if seasonality else []
            }
            productos_resumen.append(prod_data)
            index_historicos[nombre_legible] = f"data/historicos/{filepath.name}"

        # Ordenar productos alfabéticamente
        productos_resumen.sort(key=lambda x: x["nombre"])

        # Guardar productos.json
        with open(self.productos_json, "w", encoding="utf-8") as f:
            json.dump(productos_resumen, f, ensure_ascii=False, indent=2)

        # Guardar historicos_index.json
        with open(self.historicos_index_json, "w", encoding="utf-8") as f:
            json.dump(index_historicos, f, ensure_ascii=False, indent=2)

        # Guardar estacionalidad.json
        with open(self.estacionalidad_json, "w", encoding="utf-8") as f:
            json.dump(estacionalidad_global, f, ensure_ascii=False, indent=2)

        # Calcular resumen global
        if todos_los_precios and fechas_globales:
            todos_los_precios_sorted = sorted(todos_los_precios)
            n = len(todos_los_precios_sorted)
            mediana = todos_los_precios_sorted[n // 2] if n % 2 != 0 else (todos_los_precios_sorted[n // 2 - 1] + todos_los_precios_sorted[n // 2]) / 2

            ultima_actualizacion = datetime.now()
            resumen_global = {
                "ultima_actualizacion": ultima_actualizacion.isoformat(),
                "fecha_legible": ultima_actualizacion.strftime("%d de %B de %Y, %H:%M"),
                "total_productos": len(productos_resumen),
                "total_registros": total_registros_global,
                "rango_fechas": {
                    "inicio": min(fechas_globales).isoformat(),
                    "fin": max(fechas_globales).isoformat()
                },
                "estadisticas": {
                    "precio_promedio": round(sum(todos_los_precios) / len(todos_los_precios), 2),
                    "precio_minimo": round(min(todos_los_precios), 2),
                    "precio_maximo": round(max(todos_los_precios), 2),
                    "precio_mediana": round(mediana, 2)
                },
                "version": "1.0",
                "fuente": "Consejo Nacional de Producción - Costa Rica"
            }
            with open(self.resumen_json, "w", encoding="utf-8") as f:
                json.dump(resumen_global, f, ensure_ascii=False, indent=2)

        return {
            "total_productos": len(productos_resumen),
            "total_registros": total_registros_global,
            "estacionalidad_generada": len(estacionalidad_global)
        }
