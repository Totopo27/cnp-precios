"""
Bot de Telegram para CNP Precios Costa Rica.
Soporta comandos /precio, /temporada, /tendencia y consultas en texto plano.
"""
import os
import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.bot.services import BotQueryService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Instancia global del servicio de consultas
query_service = BotQueryService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mensaje de bienvenida y ayuda."""
    mensaje = (
        "👋 ¡Hola! bienvenido al *Bot de Precios del CNP Costa Rica*.\n\n"
        "Te puedo ayudar a consultar precios actualizados, tendencias de mercado y temporadas de cosecha.\n\n"
        "📌 *Comandos Disponibles:*\n"
        "• `/precio <producto>` - Consulta el precio y estacionalidad de un producto.\n"
        "• `/temporada` - Muestra los productos en oferta / temporada de cosecha.\n"
        "• `/tendencia` - Muestra los productos con mayor subida y bajada.\n"
        "• `/ayuda` - Muestra este mensaje de ayuda.\n\n"
        "💡 *Consejo:* ¡Simplemente escribí el nombre de cualquier producto (ej: `aguacate`, `tomate`, `papa`) y te daré la información de inmediato!"
    )
    if update.message:
        await update.message.reply_text(mensaje, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Alias para /start."""
    await start_command(update, context)


async def precio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /precio <producto>."""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Por favor especifica un producto. Ejemplo: `/precio aguacate`",
            parse_mode="Markdown"
        )
        return

    busqueda = " ".join(context.args)
    respuesta = query_service.query_product(busqueda)
    await update.message.reply_text(respuesta, parse_mode="Markdown")


async def temporada_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /temporada."""
    if not update.message:
        return
    respuesta = query_service.get_seasonal_recommendations()
    await update.message.reply_text(respuesta, parse_mode="Markdown")


async def tendencia_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /tendencia."""
    if not update.message:
        return
    respuesta = query_service.get_trends_summary()
    await update.message.reply_text(respuesta, parse_mode="Markdown")


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador de mensajes de texto libres sin comando."""
    if not update.message or not update.message.text:
        return

    texto = update.message.text.strip()
    respuesta = query_service.query_product(texto)
    await update.message.reply_text(respuesta, parse_mode="Markdown")


def run_telegram_bot(token: Optional[str] = None):
    """Inicializa y ejecuta el bot en modo Polling."""
    bot_token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("[Error] Debes configurar la variable de entorno TELEGRAM_BOT_TOKEN.")
        return

    print("🚀 Iniciando Bot de Telegram CNP Precios en modo Polling...")
    app = ApplicationBuilder().token(bot_token).build()

    # Registrar handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ayuda", help_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("precio", precio_command))
    app.add_handler(CommandHandler("temporada", temporada_command))
    app.add_handler(CommandHandler("tendencia", tendencia_command))

    # Handler para texto libre (excluye comandos)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_message_handler))

    app.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
