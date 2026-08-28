"""
Servicio de negocio para consulta de precios y estacionalidad desde Telegram.
"""
import json
from typing import Optional, Dict, Any, List
from src.config import PRODUCTOS_JSON, ESTACIONALIDAD_JSON
from src.core.alias_matcher import ProductAliasMatcher


class BotQueryService:
    """
    Procesa las consultas de productos y formatea las respuestas para el Bot de Telegram.
    """

    def __init__(self):
        self.productos = self._load_json(PRODUCTOS_JSON) or []
        self.estacionalidad = self._load_json(ESTACIONALIDAD_JSON) or {}
        
        # Mapeo por nombre de producto
        self.mapa_productos = {p["nombre"]: p for p in self.productos}
        self.alias_matcher = ProductAliasMatcher(list(self.mapa_productos.keys()))

    def _load_json(self, path) -> Optional[Any]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[BotService Error] No se pudo cargar {path}: {e}")
        return None

    def reload_data(self):
        """Refresca los datos en memoria tras una actualización del pipeline ETL."""
        self.productos = self._load_json(PRODUCTOS_JSON) or []
        self.estacionalidad = self._load_json(ESTACIONALIDAD_JSON) or {}
        self.mapa_productos = {p["nombre"]: p for p in self.productos}
        self.alias_matcher = ProductAliasMatcher(list(self.mapa_productos.keys()))

    def query_product(self, query: str) -> str:
        """
        Busca un producto por coincidencia exacta o difusa y formatea la respuesta en Telegram Markdown.
        """
        matches = self.alias_matcher.search(query, limit=3)
        if not matches:
            return f"❌ No encontré ningún producto que coincida con *'{query}'*.\nPrueba escribiendo por ejemplo: `aguacate`, `tomate` o `papa`."

        # Si hay múltiples coincidencias cercanas y el score del primero no es 1.0
        oficial, score = matches[0]
        prod = self.mapa_productos.get(oficial)
        if not prod:
            return "❌ Ocurrió un error consultando el detalle del producto."

        # Tendencia emoji
        trend_emoji = "➡️"
        if prod["tendencia_tipo"] == "subida":
            trend_emoji = "📈"
        elif prod["tendencia_tipo"] == "bajada":
            trend_emoji = "📉"

        # Estacionalidad info
        est = self.estacionalidad.get(oficial, {})
        estado_temp = est.get("estado_temporada_actual", "normal")
        meses_baratos = ", ".join(est.get("meses_baratos", [])) or "No disponible"

        badge_temp = "🟢 *En Oferta de Temporada*" if estado_temp == "temporada_baja" else (
            "🔴 *En Pico de Precio (Escasez)*" if estado_temp == "temporada_alta" else "🟡 *Precio Normal*"
        )

        sugerencia_coincidencia = ""
        if len(matches) > 1 and score < 1.0:
            sugerencia_coincidencia = f"\n\n_¿No era este? También encontré: {', '.join([m[0] for m in matches[1:]])}_"

        response = (
            f"🛒 *{prod['nombre']}*\n\n"
            f"💰 *Precio Actual:* ₡{prod['precio_actual']:,.2f}\n"
            f"{trend_emoji} *Tendencia:* {prod['tendencia_porcentaje']:+.1f}% ({prod['tendencia_tipo']})\n"
            f"📊 *Precio Promedio:* ₡{prod['precio_promedio']:,.2f}\n"
            f"📉 *Mínimo Histórico:* ₡{prod['precio_minimo']:,.2f}\n"
            f"📈 *Máximo Histórico:* ₡{prod['precio_maximo']:,.2f}\n\n"
            f"{badge_temp}\n"
            f"🗓️ *Meses con mejores precios:* {meses_baratos}"
            f"{sugerencia_coincidencia}"
        )

        return response

    def get_seasonal_recommendations(self) -> str:
        """Retorna la lista de productos que están actualmente en temporada baja (oferta/cosecha)."""
        ofertas = [p for p in self.productos if p.get("estado_temporada") == "temporada_baja"]
        
        if not ofertas:
            # Mostrar los 5 productos con mayor porcentaje de bajada
            en_bajada = sorted(self.productos, key=lambda x: x["tendencia_porcentaje"])[:5]
            lineas = [f"• *{p['nombre']}*: ₡{p['precio_actual']:,.2f} ({p['tendencia_porcentaje']:+.1f}%)" for p in en_bajada]
            return "🌱 *Productos con mayor baja de precio esta semana:*\n\n" + "\n".join(lineas)

        lineas = []
        for p in ofertas:
            est = self.estacionalidad.get(p["nombre"], {})
            desc = est.get("descuento_estimado_porcentaje", 0.0)
            lineas.append(f"• *{p['nombre']}*: ₡{p['precio_actual']:,.2f} (~{desc}% más barato que el promedio)")

        return "🌿 *Productos actualmente en Temporada de Cosecha (Precios Bajos):*\n\n" + "\n".join(lineas)

    def get_trends_summary(self) -> str:
        """Resumen de productos en mayor subida y bajada."""
        subida = sorted([p for p in self.productos if p["tendencia_tipo"] == "subida"], key=lambda x: x["tendencia_porcentaje"], reverse=True)[:5]
        bajada = sorted([p for p in self.productos if p["tendencia_tipo"] == "bajada"], key=lambda x: x["tendencia_porcentaje"])[:5]

        res = "📊 *Resumen Semanal de Tendencias CNP*\n\n"
        res += "📈 *Mayor Subida:*\n"
        if subida:
            for p in subida:
                res += f"• {p['nombre']}: ₡{p['precio_actual']:,.2f} ({p['tendencia_porcentaje']:+.1f}%)\n"
        else:
            res += "• Ningún producto en subida significativa.\n"

        res += "\n📉 *Mayor Bajada:*\n"
        if bajada:
            for p in bajada:
                res += f"• {p['nombre']}: ₡{p['precio_actual']:,.2f} ({p['tendencia_porcentaje']:+.1f}%)\n"
        else:
            res += "• Ningún producto en bajada significativa.\n"

        return res
