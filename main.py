"""
Punto de entrada principal para ejecutar la ingesta y publicación de datos CNP Precios,
o iniciar el Bot de Telegram.
"""
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional

from src.config import RAW_DOWNLOADS_DIR
from src.scraper.cnp_scraper import CNPScraper
from src.etl.parser import CNPParser
from src.etl.publisher import DataPublisher
from src.bot.telegram_bot import run_telegram_bot


def parse_date_from_filename(filepath: Path) -> Optional[datetime]:
    """Extrae la fecha o semana ISO a partir del nombre del archivo PDF del CNP."""
    name = filepath.name

    # Patrón 1: PNS_Ferias_51_24-12-2021.pdf
    match_date = re.search(r"(\d{2})-(\d{2})-(\d{4})", name)
    if match_date:
        day = int(match_date.group(1))
        month = int(match_date.group(2))
        year = int(match_date.group(3))
        try:
            return datetime(year, month, day)
        except ValueError:
            pass

    # Patrón 2: PNS_Ferias_35_semana_35_2026.pdf
    match_week = re.search(r"semana_(\d+)_(\d{4})", name, re.IGNORECASE)
    if match_week:
        week = int(match_week.group(1))
        year = int(match_week.group(2))
        try:
            return datetime.fromisocalendar(year, week, 5)
        except ValueError:
            pass

    return None


def cleanup_raw_downloads():
    """Elimina todos los archivos PDF temporales en data_raw/ para liberar espacio en disco."""
    if not RAW_DOWNLOADS_DIR.exists():
        return

    archivos_eliminados = 0
    bytes_liberados = 0

    for file_path in RAW_DOWNLOADS_DIR.glob("*"):
        if file_path.is_file():
            try:
                bytes_liberados += file_path.stat().st_size
                file_path.unlink()
                archivos_eliminados += 1
            except Exception as e:
                print(f"[Warning] No se pudo eliminar {file_path.name}: {e}")

    mb_liberados = round(bytes_liberados / (1024 * 1024), 2)
    print(f"-> Limpieza completada: {archivos_eliminados} archivos temporales eliminados ({mb_liberados} MB liberados).")


def run_etl():
    print("=" * 60)
    print("CNP Precios Costa Rica - Pipeline Ingesta & ETL (2021 - 2026)")
    print("=" * 60)

    # 1. Scraper
    scraper = CNPScraper()
    print("\n[1/4] Buscando boletines semanales de Ferias del Agricultor (2021-2026)...")
    bulletin_tuples = scraper.generate_weekly_feria_urls()
    print(f"-> Encontrados {len(bulletin_tuples)} boletines semanales en el servidor CNP.")

    downloaded_files = []
    for url, fecha in bulletin_tuples:
        file_path = scraper.download_file(url)
        if file_path:
            downloaded_files.append((file_path, fecha))

    # 2. Parsing de PDFs e ingesta de datos
    print(f"\n[2/4] Procesando {len(downloaded_files)} archivos PDF e ingiriendo datos...")
    parser = CNPParser()
    publisher = DataPublisher()

    registros_por_producto = defaultdict(list)

    for file_path, fecha_estimada in downloaded_files:
        try:
            fecha_boletin = parse_date_from_filename(file_path) or fecha_estimada
            datos = parser.parse_pdf(file_path, fecha_boletin)
            for producto, precio in datos.items():
                registros_por_producto[producto].append((fecha_boletin, precio))
        except Exception as e:
            print(f"[Warning] Error procesando {file_path.name}: {e}")

    # Actualizar historiales por producto
    for producto, registros in registros_por_producto.items():
        publisher.update_product_history(producto, registros)

    # 3. Reconstrucción de métricas globales y estacionalidad
    print("\n[3/4] Reconstruyendo estadísticas globales y estacionalidad...")
    stats = publisher.rebuild_all_summaries()
    print(f"-> Proceso completado exitosamente:")
    print(f"   • Total productos actualizados: {stats['total_productos']}")
    print(f"   • Total registros históricos: {stats['total_registros']}")
    print(f"   • Análisis de estacionalidad generado para {stats['estacionalidad_generada']} productos.")

    # 4. Limpieza de archivos temporales
    print("\n[4/4] Optimizando almacenamiento de disco...")
    cleanup_raw_downloads()

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="CNP Precios - CLI & Bot")
    parser.add_argument("--bot", action="store_true", help="Iniciar el Bot de Telegram")
    parser.add_argument("--token", type=str, help="Token del Bot de Telegram (opcional)")
    parser.add_argument("--cleanup", action="store_true", help="Limpiar carpeta temporal de descargas")
    args = parser.parse_args()

    if args.bot:
        run_telegram_bot(token=args.token)
    elif args.cleanup:
        cleanup_raw_downloads()
    else:
        run_etl()


if __name__ == "__main__":
    main()
