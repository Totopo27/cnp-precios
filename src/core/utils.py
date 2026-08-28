"""
Funciones de utilidad para manipulación de textos, fechas y métricas estadísticas.
"""
import re
import unicodedata

def slugify_product_name(nombre: str) -> str:
    """
    Convierte el nombre de un producto al formato de archivo histórico.
    Ejemplo: 'Aguacate Hass Nacional' -> 'Aguacate_hass_nacional'
    """
    # Eliminar caracteres no válidos para rutas (slashes, colons, etc.)
    limpio = re.sub(r'[\\/:*?"<>|]', '', nombre.strip())
    # Normalizar espacios
    limpio = re.sub(r'\s+', '_', limpio)
    partes = limpio.split('_')
    if not partes:
        return limpio
    
    resultado = [partes[0].capitalize()] + [p.lower() for p in partes[1:]]
    return "_".join(resultado)


def calculate_trend(precio_actual: float, precio_anterior: float, umbral: float = 2.0) -> tuple[float, str]:
    """
    Calcula el porcentaje de variación de precio y su clasificación.
    - umbral: Porcentaje mínimo para considerar subida o bajada (por defecto 2.0%)
    """
    if precio_anterior <= 0:
        return 0.0, "estable"
    
    variacion_pct = round(((precio_actual - precio_anterior) / precio_anterior) * 100, 1)
    
    if variacion_pct > umbral:
        tipo = "subida"
    elif variacion_pct < -umbral:
        tipo = "bajada"
    else:
        tipo = "estable"
        
    return variacion_pct, tipo
