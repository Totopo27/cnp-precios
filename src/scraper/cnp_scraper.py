"""
Scraper enfocado exclusivamente en Precios Nacionales de Ferias del Agricultor (CNP Costa Rica).
Genera y valida URLs semanales oficiales de boletines PDF desde 2021 hasta 2026.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import urllib.parse
import concurrent.futures

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

from src.config import CNP_SIM_URLS, RAW_DOWNLOADS_DIR


class CNPScraper:
    """
    Rastrea y descarga boletines semanales de Precios Nacionales de Ferias del Agricultor del CNP.
    """

    def __init__(self, target_urls: Optional[List[str]] = None, download_dir: Path = RAW_DOWNLOADS_DIR):
        self.target_urls = target_urls or CNP_SIM_URLS
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def generate_weekly_feria_urls(self, years: Optional[List[int]] = None) -> List[Tuple[str, datetime]]:
        """
        Genera y valida URLs directas de boletines semanales de Ferias del Agricultor (2021 a 2026).
        Retorna lista de tuplas (url, fecha_estimada).
        """
        if not requests:
            raise RuntimeError("requests es requerido.")

        if not years:
            current_year = datetime.now().year
            years = list(range(2021, current_year + 1))

        candidates = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        current_year = datetime.now().year
        current_week = datetime.now().isocalendar()[1]

        for year in years:
            max_week = current_week if year == current_year else 52
            for week in range(1, max_week + 1):
                try:
                    fecha = datetime.fromisocalendar(year, week, 5) # Viernes
                except ValueError:
                    continue

                date_str = fecha.strftime("%d-%m-%Y")
                w_str2 = f"{week:02d}"

                # Patrones reales del servidor CNP (2021-2026)
                url_pattern_1 = f"https://www.cnp.go.cr/sim/precios/precios_nacionales/ferias/{year}/PNS_Ferias_{w_str2}_{date_str}.pdf"
                url_pattern_2 = f"https://www.cnp.go.cr/sim/precios/precios_nacionales/ferias/{year}/PNS_Ferias_{week}_{date_str}.pdf"
                url_pattern_3 = f"https://www.cnp.go.cr/sim/precios/precios_nacionales/ferias/{year}/PNS_Ferias_{week}_semana_{week}_{year}.pdf"

                candidates.append((url_pattern_1, fecha))
                candidates.append((url_pattern_2, fecha))
                candidates.append((url_pattern_3, fecha))

        # Validar disponibilidad HTTP HEAD en paralelo
        valid_bulletins = []
        def check_candidate(item):
            url, fecha = item
            try:
                r = requests.head(url, headers=headers, timeout=4)
                if r.status_code == 200:
                    return (url, fecha)
            except Exception:
                pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            results = list(executor.map(check_candidate, candidates))

        for res in results:
            if res and res not in valid_bulletins:
                valid_bulletins.append(res)

        return valid_bulletins

    def fetch_bulletin_links(self) -> List[str]:
        """Obtiene URLs de boletines semanales validando estructura directa."""
        weekly = self.generate_weekly_feria_urls()
        urls = [item[0] for item in weekly]
        return urls

    def download_file(self, url: str) -> Optional[Path]:
        """Descarga un boletín oficial de Ferias del Agricultor."""
        if not requests:
            raise RuntimeError("requests no está instalado.")

        filename = Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name
        if not filename or filename.endswith(".aspx"):
            filename = f"boletin_ferias_{abs(hash(url))}.pdf"

        dest_path = self.download_dir / filename
        if dest_path.exists():
            return dest_path

        try:
            print(f"[Scraper] Descargando Boletín Feria: {filename}...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = requests.get(url, headers=headers, timeout=30)
            res.raise_for_status()
            with open(dest_path, "wb") as f:
                f.write(res.content)
            return dest_path
        except Exception as e:
            print(f"[Scraper Error] Error descargando {url}: {e}")
            return None
