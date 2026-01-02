"""
Data Acquirer - Scraper RSS de Noticias Económicas
Obtiene noticias con fechas reales de publicación
"""

import feedparser
import json
import os
import logging
from datetime import datetime, timedelta

# ---------------- CONFIGURACIÓN ---------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

RSS_FEEDS = {
    "portafolio.co": "https://www.portafolio.co/rss",
    "larepublica.co": "https://www.larepublica.co/rss",
    "banrep.gov.co": "https://www.banrep.gov.co/es/rss/noticias"
}

# ---------------- SCRAPER ---------------- #

class NoticiasRSSScraper:

    def __init__(self, dias_atras=7):
        self.noticias = []
        self.doc_id = 1
        self.dias_atras = dias_atras
        self.fecha_limite = datetime.now() - timedelta(days=dias_atras)

        logger.info(
            f"Buscando noticias desde {self.fecha_limite.date()} hasta hoy"
        )

    def _fecha_en_rango(self, fecha):
        return fecha >= self.fecha_limite

    def _parsear_fecha_entry(self, entry):
        """
        Convierte la fecha del RSS a datetime
        """
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])

        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])

        return None

    def _procesar_feed(self, fuente, url):
        logger.info(f"Descargando RSS: {fuente}")

        feed = feedparser.parse(url)

        if feed.bozo:
            logger.warning(f"RSS inválido o con errores: {fuente}")
            return

        for entry in feed.entries:
            fecha = self._parsear_fecha_entry(entry)
            if not fecha:
                continue

            if not self._fecha_en_rango(fecha):
                continue

            titulo = entry.title.strip()
            descripcion = getattr(entry, "summary", "").strip()

            texto = f"{titulo}. {descripcion}" if descripcion else titulo

            noticia = {
                "id": str(self.doc_id),
                "date": fecha.strftime("%Y-%m-%d"),
                "text": texto,
                "source": fuente,
                "url": entry.link
            }

            self.noticias.append(noticia)
            self.doc_id += 1

            logger.info(f"✓ [{noticia['date']}] {titulo[:60]}")

    def descargar_noticias(self):
        logger.info("=" * 70)
        logger.info(f"DESCARGANDO NOTICIAS RSS - ÚLTIMOS {self.dias_atras} DÍAS")
        logger.info("=" * 70)

        for fuente, url in RSS_FEEDS.items():
            self._procesar_feed(fuente, url)

    def guardar_noticias(self):
        if not self.noticias:
            logger.warning("No hay noticias para guardar")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            OUTPUT_DIR, f"noticias_rss_{timestamp}.jsonl"
        )

        with open(filename, "w", encoding="utf-8") as f:
            for noticia in self.noticias:
                f.write(json.dumps(noticia, ensure_ascii=False) + "\n")

        logger.info(
            f"✅ Guardadas {len(self.noticias)} noticias en {filename}"
        )
        return filename

    def mostrar_estadisticas(self):
        if not self.noticias:
            print("\n⚠️ No se descargaron noticias")
            return

        por_fuente = {}
        por_fecha = {}

        for n in self.noticias:
            por_fuente[n["source"]] = por_fuente.get(n["source"], 0) + 1
            por_fecha[n["date"]] = por_fecha.get(n["date"], 0) + 1

        print("\n" + "=" * 70)
        print("ESTADÍSTICAS")
        print("=" * 70)
        print(f"Total de noticias: {len(self.noticias)}\n")

        print("Por fuente:")
        for f, c in por_fuente.items():
            print(f"  - {f}: {c}")

        print("\nPor fecha:")
        for f in sorted(por_fecha.keys(), reverse=True):
            print(f"  - {f}: {por_fecha[f]} noticias")

        print("=" * 70)

# ---------------- MAIN ---------------- #

def main():
    print("=" * 70)
    print("DATA ACQUIRER - Noticias Económicas (RSS)")
    print("=" * 70)

    scraper = NoticiasRSSScraper(dias_atras=7)
    scraper.descargar_noticias()

    if scraper.noticias:
        scraper.guardar_noticias()
        scraper.mostrar_estadisticas()
        print("\n✅ Pipeline RSS completado con éxito\n")
        return 0
    else:
        print("\n⚠️ No se encontraron noticias en el rango\n")
        return 1

if __name__ == "__main__":
    exit(main())