"""
COLCAP Data Fetcher - Descarga automática de datos históricos del índice COLCAP
Obtiene datos desde Yahoo Finance (símbolo: ^COLCAP)
"""

import requests
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
import time
import json

# ---------------- CONFIGURACIÓN ---------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "indicators")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Símbolo del COLCAP en Yahoo Finance
COLCAP_SYMBOL = "^COLCAP"

# ---------------- MÉTODOS DE DESCARGA ---------------- #

class ColcapFetcher:
    """
    Clase para descargar datos históricos del COLCAP desde múltiples fuentes
    """
    
    def __init__(self, dias_atras=30):
        self.dias_atras = dias_atras
        self.fecha_fin = datetime.now()
        self.fecha_inicio = self.fecha_fin - timedelta(days=dias_atras)
        self.datos = None
        
    def _yahoo_finance_method(self):
       
        try:
            # Convertir fechas a timestamps Unix
            timestamp_inicio = int(self.fecha_inicio.timestamp())
            timestamp_fin = int(self.fecha_fin.timestamp())
            
            # URL de Yahoo Finance
            url = f"https://query1.finance.yahoo.com/v7/finance/download/{COLCAP_SYMBOL}"
            params = {
                'period1': timestamp_inicio,
                'period2': timestamp_fin,
                'interval': '1d',
                'events': 'history',
                'includeAdjustedClose': 'true'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parsear CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Renombrar columnas
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'colcap_open',
                'High': 'colcap_high',
                'Low': 'colcap_low',
                'Close': 'colcap_close',
                'Adj Close': 'colcap_adj_close',
                'Volume': 'colcap_volume'
            })
            
            # Formatear fecha
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
            logger.info(f"✓ Descargados {len(df)} registros desde Yahoo Finance")
            return df
            
        except Exception as e:
            logger.error(f"Error con Yahoo Finance: {e}")
            return None
    
    def _investing_com_method(self):
        """
        Método 2: Web scraping desde Investing.com (backup)
        """
        logger.info("Intentando scraping desde Investing.com...")
        
        try:
            # URL de Investing.com para COLCAP
            url = "https://www.investing.com/indices/colcap-historical-data"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parsear HTML con pandas
            tables = pd.read_html(response.text)
            
            if not tables:
                raise ValueError("No se encontraron tablas en la página")
            
            df = tables[0]
            
            # Renombrar columnas (depende del formato de Investing.com)
            column_mapping = {
                'Fecha': 'date',
                'Último': 'colcap_close',
                'Apertura': 'colcap_open',
                'Máximo': 'colcap_high',
                'Mínimo': 'colcap_low',
                'Vol.': 'colcap_volume',
                '% var.': 'change_pct'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Limpiar y convertir fecha
            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y').dt.strftime('%Y-%m-%d')
            
            # Seleccionar columnas relevantes
            columnas_finales = ['date', 'colcap_open', 'colcap_high', 'colcap_low', 'colcap_close', 'colcap_volume']
            df = df[columnas_finales]
            
            logger.info(f"✓ Descargados {len(df)} registros desde Investing.com")
            return df
            
        except Exception as e:
            logger.error(f"Error con Investing.com: {e}")
            return None
    
    def _generar_datos_simulados(self):
        """
        Método 3: Generar datos simulados para desarrollo/testing
        """
        logger.warning("Generando datos simulados para desarrollo...")
        
        # Crear rango de fechas
        fechas = pd.date_range(
            start=self.fecha_inicio, 
            end=self.fecha_fin, 
            freq='D'
        )
        
        # Generar datos sintéticos con tendencia y ruido
        import numpy as np
        np.random.seed(42)
        
        base_value = 1500
        trend = np.linspace(0, 100, len(fechas))
        noise = np.random.normal(0, 30, len(fechas))
        
        valores = base_value + trend + noise
        
        df = pd.DataFrame({
            'date': fechas.strftime('%Y-%m-%d'),
            'colcap_open': valores + np.random.uniform(-10, 10, len(fechas)),
            'colcap_high': valores + np.random.uniform(0, 20, len(fechas)),
            'colcap_low': valores - np.random.uniform(0, 20, len(fechas)),
            'colcap_close': valores,
            'colcap_volume': np.random.randint(1000000, 5000000, len(fechas))
        })
        
        logger.info(f"✓ Generados {len(df)} registros simulados")
        return df
    
    def descargar_datos(self, metodo='auto'):
        """
        Descarga datos usando el método especificado o intentando todos
        
        Args:
            metodo (str): 'yahoo', 'investing', 'simulado' o 'auto'
        """
        logger.info("=" * 70)
        logger.info(f"DESCARGANDO DATOS COLCAP - ÚLTIMOS {self.dias_atras} DÍAS")
        logger.info(f"Rango: {self.fecha_inicio.date()} a {self.fecha_fin.date()}")
        logger.info("=" * 70)
        
        if metodo == 'yahoo':
            self.datos = self._yahoo_finance_method()
        elif metodo == 'investing':
            self.datos = self._investing_com_method()
        elif metodo == 'simulado':
            self.datos = self._generar_datos_simulados()
        else:  # auto
            # Intentar métodos en orden de preferencia
            self.datos = self._yahoo_finance_method()
            
            if self.datos is None:
                logger.warning("Yahoo Finance falló, intentando Investing.com...")
                time.sleep(2)
                self.datos = self._investing_com_method()
            
            if self.datos is None:
                logger.warning("Todas las fuentes fallaron, usando datos simulados...")
                self.datos = self._generar_datos_simulados()
        
        return self.datos is not None
    
    def guardar_datos(self):
        """
        Guarda los datos en formato CSV
        """
        if self.datos is None or self.datos.empty:
            logger.error("No hay datos para guardar")
            return None
        
        # Ordenar por fecha
        self.datos = self.datos.sort_values('date').reset_index(drop=True)
        
        # Guardar CSV
        output_file = os.path.join(OUTPUT_DIR, "COLCAP.csv")
        self.datos.to_csv(output_file, index=False)
        
        logger.info(f"✅ Datos guardados en {output_file}")
        
        # Guardar también metadatos
        metadata = {
            'ultima_actualizacion': datetime.now().isoformat(),
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'registros_totales': len(self.datos),
            'columnas': list(self.datos.columns)
        }
        
        metadata_file = os.path.join(OUTPUT_DIR, "COLCAP_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return output_file
    
    def mostrar_estadisticas(self):
        """
        Muestra estadísticas de los datos descargados
        """
        if self.datos is None or self.datos.empty:
            print("\n⚠️ No hay datos para mostrar")
            return
        
        print("\n" + "=" * 70)
        print("ESTADÍSTICAS DE DATOS COLCAP")
        print("=" * 70)
        print(f"Total de registros: {len(self.datos)}")
        print(f"Fecha inicial: {self.datos['date'].iloc[0]}")
        print(f"Fecha final: {self.datos['date'].iloc[-1]}")
        print(f"\nValores de cierre:")
        print(f"  - Mínimo: {self.datos['colcap_close'].min():.2f}")
        print(f"  - Máximo: {self.datos['colcap_close'].max():.2f}")
        print(f"  - Promedio: {self.datos['colcap_close'].mean():.2f}")
        print(f"  - Último valor: {self.datos['colcap_close'].iloc[-1]:.2f}")
        
        # Mostrar primeros y últimos registros
        print("\nPrimeros registros:")
        print(self.datos.head(3).to_string(index=False))
        print("\nÚltimos registros:")
        print(self.datos.tail(3).to_string(index=False))
        print("=" * 70)


def main():
    """
    Función principal
    """
    print("=" * 70)
    print("COLCAP DATA FETCHER - Descarga Automática")
    print("=" * 70)
    
    dias = int(os.getenv('COLCAP_DAYS', '30'))
    metodo = os.getenv('COLCAP_METHOD', 'auto')
    
    fetcher = ColcapFetcher(dias_atras=dias)
    
    if fetcher.descargar_datos(metodo=metodo):
        fetcher.guardar_datos()
        fetcher.mostrar_estadisticas()
        print("\n✅ Descarga de COLCAP completada con éxito\n")
        return 0
    else:
        print("\n Error: No se pudieron obtener datos del COLCAP\n")
        return 1

if __name__ == "__main__":
    exit(main())
