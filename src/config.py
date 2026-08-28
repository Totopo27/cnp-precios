"""
Configuraciones globales del sistema CNP Precios.
"""
from pathlib import Path

# Directorios del Proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = DOCS_DIR / "data"
HISTORICOS_DIR = DATA_DIR / "historicos"
RAW_DOWNLOADS_DIR = BASE_DIR / "data_raw"

# Asegurar que existan los directorios
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORICOS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Archivos clave
PRODUCTOS_JSON = DATA_DIR / "productos.json"
RESUMEN_JSON = DATA_DIR / "resumen.json"
HISTORICOS_INDEX_JSON = DATA_DIR / "historicos_index.json"
ESTACIONALIDAD_JSON = DATA_DIR / "estacionalidad.json"

# Fuente Exclusiva: Precios Nacionales de Ferias del Agricultor (CNP Costa Rica)
CNP_SIM_URLS = [
    "https://www.cnp.go.cr/sim/Precios_Nac_Ferias_del_Agricultor.aspx"
]
