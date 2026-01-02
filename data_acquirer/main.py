"""
Data Acquirer Master - Ejecuta descarga de noticias y datos COLCAP
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from scraper import main as scraper_main
from colcap_fetcher import main as colcap_main

def main():
    print("=" * 70)
    print("DATA ACQUIRER MASTER - Pipeline Completo")
    print("=" * 70)
    print()
    
    # 1. Descargar noticias
    print("PASO 1: Descargando noticias RSS...")
    print("-" * 70)
    try:
        resultado_noticias = scraper_main()
        if resultado_noticias != 0:
            print("⚠️  Warning: El scraper de noticias tuvo problemas")
    except Exception as e:
        print(f"❌ Error en scraper de noticias: {e}")
        resultado_noticias = 1
    
    print()
    
    # 2. Descargar datos COLCAP
    print("PASO 2: Descargando datos COLCAP...")
    print("-" * 70)
    try:
        resultado_colcap = colcap_main()
        if resultado_colcap != 0:
            print("⚠️  Warning: El fetcher de COLCAP tuvo problemas")
    except Exception as e:
        print(f"❌ Error en fetcher de COLCAP: {e}")
        resultado_colcap = 1
    
    print()
    print("=" * 70)
    
    if resultado_noticias == 0 and resultado_colcap == 0:
        print("✅ DATA ACQUIRER COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        return 0
    elif resultado_noticias == 0 or resultado_colcap == 0:
        print("⚠️  DATA ACQUIRER COMPLETADO CON ADVERTENCIAS")
        print("=" * 70)
        return 0
    else:
        print("❌ DATA ACQUIRER FALLÓ")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    exit(main())
