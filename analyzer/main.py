"""
Analyzer Main - Análisis de datos procesados y API
Compatible con ejecución desde cualquier directorio
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
import logging
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Detectar desde dónde se ejecuta y ajustar rutas
if os.path.basename(os.getcwd()) == 'analyzer':
    # Se ejecuta desde analyzer/, subir un nivel
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(BASE_DIR)
    logger.info(f"📁 Cambiando directorio de trabajo a: {BASE_DIR}")
else:
    # Se ejecuta desde la raíz
    BASE_DIR = os.getcwd()

PROCESSED_PATH = "data/processed"
INDICATORS_PATH = "data/indicators"
OUTPUT_PATH = "data/aggregated"
PLOTS_PATH = os.path.join(OUTPUT_PATH, "plots")

os.makedirs(OUTPUT_PATH, exist_ok=True)
os.makedirs(PLOTS_PATH, exist_ok=True)

def load_processed_data():
    """Carga datos procesados del processor"""
    logger.info("Cargando datos procesados...")
    results_path = os.path.join(PROCESSED_PATH, "results.csv")
    
    # Mostrar ruta absoluta para debug
    abs_path = os.path.abspath(results_path)
    logger.info(f"  Buscando: {abs_path}")
    
    if not os.path.exists(results_path):
        logger.error(f"❌ No se encontró {results_path}")
        logger.error(f"   Ruta absoluta: {abs_path}")
        logger.error(f"   El processor debe ejecutarse primero")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(results_path)
        logger.info(f"✓ Cargados {len(df)} registros procesados")
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        logger.info(f"  Columnas: {list(df.columns)}")
        logger.info(f"  Rango: {df['date'].min()} a {df['date'].max()}")
        
        return df
    except Exception as e:
        logger.error(f"❌ Error leyendo {results_path}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def load_colcap_data():
    """Carga datos del índice COLCAP"""
    logger.info("Cargando datos COLCAP...")
    colcap_path = os.path.join(INDICATORS_PATH, "COLCAP.csv")
    
    # Mostrar ruta absoluta para debug
    abs_path = os.path.abspath(colcap_path)
    logger.info(f"  Buscando: {abs_path}")
    
    if not os.path.exists(colcap_path):
        logger.warning(f"⚠️  No se encontró {colcap_path}")
        logger.warning(f"   Continuando sin datos COLCAP")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(colcap_path)
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        if 'colcap_close' not in df.columns:
            logger.error(f"❌ El archivo COLCAP.csv no tiene la columna 'colcap_close'")
            logger.error(f"   Columnas encontradas: {list(df.columns)}")
            return pd.DataFrame()
        
        logger.info(f"✓ Cargados {len(df)} registros COLCAP")
        logger.info(f"  Columnas: {list(df.columns)}")
        logger.info(f"  Rango COLCAP: {df['date'].min()} a {df['date'].max()}")
        
        return df
    except Exception as e:
        logger.error(f"❌ Error leyendo {colcap_path}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def aggregate_by_date(df_processed):
    """Agrega datos por fecha"""
    logger.info("Agregando datos por fecha...")
    
    if df_processed.empty:
        logger.error("❌ No hay datos para agregar")
        return pd.DataFrame()
    
    try:
        # Agrupar por fecha
        daily_agg = df_processed.groupby('date').agg({
            'doc_id': 'count',
            'keyword_hits': 'sum'
        }).reset_index()
        
        daily_agg.columns = ['date', 'docs_count', 'total_keyword_hits']
        
        logger.info(f"✓ Generadas {len(daily_agg)} agregaciones diarias")
        logger.info(f"  Total documentos: {daily_agg['docs_count'].sum()}")
        logger.info(f"  Total keywords: {daily_agg['total_keyword_hits'].sum()}")
        logger.info(f"  Rango: {daily_agg['date'].min()} a {daily_agg['date'].max()}")
        
        return daily_agg
    except Exception as e:
        logger.error(f"❌ Error agregando datos: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def merge_with_colcap(daily_agg, df_colcap):
    """Fusiona datos agregados con COLCAP"""
    logger.info("Fusionando con datos COLCAP...")
    
    if daily_agg.empty:
        logger.error("❌ No hay datos agregados para fusionar")
        return pd.DataFrame()
    
    if df_colcap.empty:
        logger.warning("⚠️  No hay datos COLCAP, continuando sin ellos")
        return daily_agg
    
    try:
        merged = pd.merge(
            daily_agg,
            df_colcap,
            on='date',
            how='left'
        )
        
        logger.info(f"✓ Datos fusionados: {len(merged)} registros")
        logger.info(f"  Con COLCAP: {merged['colcap_close'].notna().sum()} registros")
        logger.info(f"  Sin COLCAP: {merged['colcap_close'].isna().sum()} registros")
        
        return merged
    except Exception as e:
        logger.error(f"❌ Error fusionando datos: {e}")
        import traceback
        traceback.print_exc()
        return daily_agg

def calculate_metrics(merged_df):
    """Calcula métricas y correlaciones"""
    logger.info("Calculando métricas...")
    
    if merged_df.empty:
        logger.error("❌ No hay datos para calcular métricas")
        return {}
    
    try:
        metrics = {
            "total_documents": int(merged_df['docs_count'].sum()),
            "total_keywords": int(merged_df['total_keyword_hits'].sum()),
            "date_range": f"{merged_df['date'].min().date()} to {merged_df['date'].max().date()}",
            "days_analyzed": len(merged_df),
            "average_docs_per_day": float(merged_df['docs_count'].mean()),
            "average_keywords_per_day": float(merged_df['total_keyword_hits'].mean())
        }
        
        # Solo calcular correlación si hay datos COLCAP
        if 'colcap_close' in merged_df.columns:
            valid_data = merged_df.dropna(subset=['colcap_close'])
            
            if len(valid_data) >= 2:
                correlation = valid_data['total_keyword_hits'].corr(valid_data['colcap_close'])
                metrics["correlation_keywords_colcap"] = float(correlation) if not np.isnan(correlation) else 0.0
                metrics["average_colcap"] = float(valid_data['colcap_close'].mean())
                metrics["colcap_min"] = float(valid_data['colcap_close'].min())
                metrics["colcap_max"] = float(valid_data['colcap_close'].max())
                metrics["days_with_colcap"] = len(valid_data)
                
                logger.info(f"✓ Correlación keywords-COLCAP: {metrics['correlation_keywords_colcap']:.4f}")
                logger.info(f"  COLCAP promedio: {metrics['average_colcap']:.2f}")
            else:
                logger.warning("⚠️  Datos insuficientes para calcular correlación")
        
        return metrics
    except Exception as e:
        logger.error(f"❌ Error calculando métricas: {e}")
        import traceback
        traceback.print_exc()
        return {}

def generate_plots(merged_df):
    """Genera gráficas de análisis"""
    logger.info("Generando gráficas...")
    
    if merged_df.empty:
        logger.warning("⚠️  No hay datos para generar gráficas")
        return
    
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        
        has_colcap = 'colcap_close' in merged_df.columns and merged_df['colcap_close'].notna().sum() > 0
        
        if has_colcap:
            fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        else:
            fig, axes = plt.subplots(1, 1, figsize=(12, 4))
            axes = [axes]
        
        # Gráfica 1: Keywords por día
        axes[0].plot(merged_df['date'], merged_df['total_keyword_hits'], 
                    marker='o', color='#2E86AB', linewidth=2, markersize=6)
        axes[0].set_title('Keywords Económicos por Día', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Fecha')
        axes[0].set_ylabel('Total Keywords')
        axes[0].grid(True, alpha=0.3)
        axes[0].tick_params(axis='x', rotation=45)
        
        if has_colcap:
            valid_colcap = merged_df.dropna(subset=['colcap_close'])
            
            # Gráfica 2: COLCAP por día
            axes[1].plot(valid_colcap['date'], valid_colcap['colcap_close'], 
                        marker='s', color='#A23B72', linewidth=2, markersize=6)
            axes[1].set_title('Índice COLCAP por Día', fontsize=14, fontweight='bold')
            axes[1].set_xlabel('Fecha')
            axes[1].set_ylabel('COLCAP (puntos)')
            axes[1].grid(True, alpha=0.3)
            axes[1].tick_params(axis='x', rotation=45)
            
            # Gráfica 3: Correlación
            if len(valid_colcap) > 1:
                axes[2].scatter(valid_colcap['total_keyword_hits'], 
                              valid_colcap['colcap_close'], 
                              alpha=0.6, color='#F18F01', s=100)
                
                z = np.polyfit(valid_colcap['total_keyword_hits'], 
                             valid_colcap['colcap_close'], 1)
                p = np.poly1d(z)
                axes[2].plot(valid_colcap['total_keyword_hits'], 
                           p(valid_colcap['total_keyword_hits']), 
                           "r--", alpha=0.8, linewidth=2, 
                           label=f'Tendencia: y={z[0]:.2f}x+{z[1]:.2f}')
                
                axes[2].set_title('Correlación: Keywords vs COLCAP', 
                                fontsize=14, fontweight='bold')
                axes[2].set_xlabel('Total Keywords')
                axes[2].set_ylabel('COLCAP (puntos)')
                axes[2].grid(True, alpha=0.3)
                axes[2].legend()
        
        plt.tight_layout()
        plot_path = os.path.join(PLOTS_PATH, 'analysis_complete.png')
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Gráficas guardadas en {plot_path}")
    except Exception as e:
        logger.error(f"❌ Error generando gráficas: {e}")
        import traceback
        traceback.print_exc()

def save_results(merged_df, metrics):
    """Guarda resultados del análisis"""
    logger.info("Guardando resultados...")
    
    if merged_df.empty:
        logger.error("❌ No hay datos para guardar")
        return
    
    try:
        # Guardar datos fusionados
        merged_path = os.path.join(OUTPUT_PATH, "merged_daily.csv")
        merged_df.to_csv(merged_path, index=False)
        logger.info(f"✓ Datos fusionados guardados en {merged_path}")
        
        # Guardar métricas
        if metrics:
            metrics_path = os.path.join(OUTPUT_PATH, "metrics.txt")
            with open(metrics_path, 'w') as f:
                for key, value in metrics.items():
                    f.write(f"{key}: {value}\n")
            logger.info(f"✓ Métricas guardadas en {metrics_path}")
    except Exception as e:
        logger.error(f"❌ Error guardando resultados: {e}")
        import traceback
        traceback.print_exc()

def analyze():
    """Ejecuta el pipeline completo de análisis"""
    logger.info("=" * 70)
    logger.info("INICIANDO ANÁLISIS DE DATOS")
    logger.info("=" * 70)
    
    df_processed = load_processed_data()
    if df_processed.empty:
        logger.error("=" * 70)
        logger.error("❌ ERROR: No hay datos procesados")
        logger.error("=" * 70)
        return None
    
    df_colcap = load_colcap_data()
    
    daily_agg = aggregate_by_date(df_processed)
    if daily_agg.empty:
        logger.error("=" * 70)
        logger.error("❌ ERROR: No se pudo agregar datos")
        logger.error("=" * 70)
        return None
    
    merged_df = merge_with_colcap(daily_agg, df_colcap)
    metrics = calculate_metrics(merged_df)
    generate_plots(merged_df)
    save_results(merged_df, metrics)
    
    logger.info("=" * 70)
    logger.info("✅ ANÁLISIS COMPLETADO")
    logger.info("=" * 70)
    
    return metrics

def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando Analyzer...")
        logger.info(f"📂 Directorio de trabajo: {os.getcwd()}")
        
        # Agregar el directorio actual al Python path
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
            logger.info(f"✓ Agregado al Python path: {os.getcwd()}")
        
        # Ejecutar análisis
        metrics = analyze()
        
        if metrics is None:
            logger.error("❌ El análisis falló")
            logger.error("   No se iniciará la API")
            return 1
        
        # Iniciar API
        logger.info("\n🌐 Iniciando API REST...")

        
        # Importar la app después de ajustar el path
        try:
            from analyzer.api import app
            logger.info("✓ Módulo analyzer.api importado correctamente")
        except ImportError as ie:
            logger.error(f"❌ Error importando analyzer.api: {ie}")
            logger.info("Intentando importación alternativa...")
            # Intento alternativo: importar directamente desde el archivo
            import importlib.util
            spec = importlib.util.spec_from_file_location("api", "analyzer/api.py")
            api_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(api_module)
            app = api_module.app
            logger.info("✓ API importada mediante método alternativo")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())