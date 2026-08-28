"""
Parser de boletines de precios del CNP (PDF, XML, Excel, CSV).
Soporta tablas de 1 y 2 columnas con expresiones regulares robustas.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pandas as pd
except ImportError:
    pd = None


class CNPParser:
    """
    Parsea boletines oficiales del CNP en diversos formatos para extraer
    precios por producto.
    """

    @staticmethod
    def clean_price(text: str) -> Optional[float]:
        """Limpia cadenas de texto con precios ('¢1,200.00', '1200', '1.200,00') -> float."""
        if not text:
            return None
        cleaned = re.sub(r"[^\d.,]", "", str(text)).strip()
        if not cleaned:
            return None
        
        # Manejo de separadores de miles/decimales ticos
        if "," in cleaned and "." in cleaned:
            if cleaned.find(",") < cleaned.find("."):
                cleaned = cleaned.replace(",", "")
            else:
                cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            parts = cleaned.split(",")
            if len(parts[-1]) == 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
                
        try:
            return float(cleaned)
        except ValueError:
            return None

    def parse_pdf(self, pdf_path: Path, fecha: datetime) -> Dict[str, float]:
        """
        Extrae datos de precios desde un PDF oficial del CNP utilizando pdfplumber.
        Soporta diseños de tablas en 1 y 2 columnas mediante regex multi-columna.
        Retorna un diccionario {nombre_producto: precio}.
        """
        if not pdfplumber:
            raise RuntimeError("pdfplumber no está instalado.")

        resultados = {}
        # Patrón regex multi-columna para boletines de Ferias del Agricultor del CNP
        regex_pattern = re.compile(
            r"([A-Za-zÁÉÍÓÚáéíóúÑñ\s/.\-]+?)\s+(?:kg|unidad|mata|rollito|manojo|caja|bolsa|docena|litro|g)\s+([\d.,]+)",
            re.IGNORECASE
        )

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                # Procesar coincidencias de productos en todas las columnas de la página
                matches = regex_pattern.findall(text)
                for prod_raw, price_raw in matches:
                    nombre = prod_raw.strip()
                    # Omitir encabezados o metadatos
                    if not nombre or any(w in nombre.lower() for w in ["boletín", "informe", "servicios de", "mercados", "área metropolitana"]):
                        continue
                    
                    precio = self.clean_price(price_raw)
                    if precio and precio > 0:
                        resultados[nombre] = precio

                # Fallback: si no extrajo nada por regex, usar extract_tables()
                if not resultados:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if not row:
                                continue
                            # Iterar pares de columnas (ej: Col 0 prod, Col 2 precio | Col 3 prod, Col 5 precio)
                            for i in range(0, len(row) - 1):
                                cell_val = str(row[i]).strip() if row[i] else ""
                                if cell_val and not any(w in cell_val.lower() for w in ["producto", "mercado", "boletín"]):
                                    for j in range(i + 1, min(i + 3, len(row))):
                                        p_val = self.clean_price(row[j])
                                        if p_val and p_val > 0:
                                            resultados[cell_val] = p_val
                                            break

        return resultados

    def parse_tabular(self, file_path: Path) -> Dict[str, float]:
        """Parsea archivos CSV o Excel (XLS/XLSX) usando pandas."""
        if not pd:
            raise RuntimeError("pandas no está instalado.")

        resultados = {}
        df = pd.read_excel(file_path) if file_path.suffix.lower() in [".xls", ".xlsx"] else pd.read_csv(file_path)
        
        # Normalizar nombres de columnas
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        col_prod = next((c for c in df.columns if "producto" in c or "nombre" in c), df.columns[0])
        col_precio = next((c for c in df.columns if "precio" in c or "promedio" in c or "frecuente" in c), df.columns[1])

        for _, row in df.iterrows():
            nombre = str(row[col_prod]).strip()
            precio = self.clean_price(row[col_precio])
            if nombre and precio and precio > 0:
                resultados[nombre] = precio

        return resultados
