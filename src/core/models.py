"""
Modelos de datos para CNP Precios (Pydantic).
"""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class PriceRecord(BaseModel):
    """Registro individual de precio con fecha."""
    fecha: datetime
    precio: float

class ProductSummary(BaseModel):
    """Resumen estadístico y estado actual de un producto."""
    nombre: str
    precio_actual: float
    precio_promedio: float
    precio_minimo: float
    precio_maximo: float
    total_registros: int
    ultima_fecha: datetime
    tendencia_porcentaje: float
    tendencia_tipo: Literal["subida", "bajada", "estable"]

class DateRange(BaseModel):
    inicio: datetime
    fin: datetime

class GlobalStatistics(BaseModel):
    precio_promedio: float
    precio_minimo: float
    precio_maximo: float
    precio_mediana: float

class GlobalSummary(BaseModel):
    """Metadatos globales del resumen de precios."""
    ultima_actualizacion: datetime
    fecha_legible: str
    total_productos: int
    total_registros: int
    rango_fechas: DateRange
    estadisticas: GlobalStatistics
    version: str = "1.0"
    fuente: str = "Consejo Nacional de Producción - Costa Rica"
