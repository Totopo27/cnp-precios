"""
Búsqueda difusa (fuzzy search) y resolución de alias para productos CNP.
"""
import difflib
import re
import unicodedata
from typing import List, Dict, Optional, Tuple


def remove_accents(text: str) -> str:
    """Elimina tildes y caracteres especiales."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()


class ProductAliasMatcher:
    """
    Resuelve consultas con errores ortográficos o abreviaturas hacia la lista oficial de productos.
    """

    def __init__(self, productos_oficiales: List[str]):
        self.productos_oficiales = productos_oficiales
        self._mapa_normalizado = {
            remove_accents(p): p for p in productos_oficiales
        }

    def search(self, query: str, limit: int = 5, cutoff: float = 0.4) -> List[Tuple[str, float]]:
        """
        Busca coincidencias para un término ingresado por el usuario.
        Retorna lista de tuplas (nombre_oficial, score).
        """
        if not query or not query.strip():
            return []

        query_norm = remove_accents(query.strip())
        
        # 1. Busqueda por subcadena exacta (ej: 'tomate' en 'tomate primera')
        coincidencias_exactas = []
        for norm, oficial in self._mapa_normalizado.items():
            if query_norm in norm or norm in query_norm:
                coincidencias_exactas.append((oficial, 1.0))

        if coincidencias_exactas:
            return coincidencias_exactas[:limit]

        # 2. Busqueda difusa con difflib
        matches = difflib.get_close_matches(
            query_norm,
            list(self._mapa_normalizado.keys()),
            n=limit,
            cutoff=cutoff
        )

        resultados = []
        for match in matches:
            ratio = difflib.SequenceMatcher(None, query_norm, match).ratio()
            oficial = self._mapa_normalizado[match]
            resultados.append((oficial, round(ratio, 2)))

        return resultados

    def get_best_match(self, query: str) -> Optional[str]:
        """Retorna la mejor coincidencia o None si no supera el umbral."""
        matches = self.search(query, limit=1)
        return matches[0][0] if matches else None
