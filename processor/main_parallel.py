"""
Módulo de procesamiento paralelo de noticias
Implementa procesamiento concurrente usando multiprocessing
"""

import json
import os
import pandas as pd
from unidecode import unidecode
from multiprocessing import Pool, cpu_count, Manager
from functools import partial
import time
import logging
from typing import List, Dict, Tuple

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Keywords para búsqueda
KEYWORDS = [
    # Macroeconomía
    "inflacion", "ipc", "pib", "crecimiento", "recesion",
    "desempleo", "consumo",

    # Política monetaria
    "tasa de interes", "tasas",
    "banco de la republica", "fed",

    # Mercados
    "bolsa", "acciones", "mercado",
    "colcap", "volatilidad",

    # Tipo de cambio
    "dolar", "trm", "divisas",

    # Commodities
    "petroleo", "brent", "oro",

    # Finanzas y riesgo
    "banco", "credito", "inversion",
    "crisis", "riesgo"
]
# Paths
INPUT_PATH = os.getenv("RAW_DATA_PATH", "data/raw")
OUTPUT_PATH = os.getenv("PROCESSED_DATA_PATH", "data/processed")

# Configuración de paralelismo
NUM_WORKERS = int(os.getenv("PROCESSOR_WORKERS", cpu_count()))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))

os.makedirs(OUTPUT_PATH, exist_ok=True)


def clean_text(text: str) -> str:
    """
    Limpia y normaliza texto para análisis.
    
    Args:
        text (str): Texto a limpiar
        
    Returns:
        str: Texto normalizado
    """
    text = unidecode(text.lower())
    # Remover caracteres especiales pero mantener espacios
    text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text)
    return text


def count_keywords(text: str, keywords: List[str]) -> int:
    """
    Cuenta ocurrencias de keywords en el texto.
    
    Args:
        text (str): Texto a analizar
        keywords (List[str]): Lista de palabras clave
        
    Returns:
        int: Número total de ocurrencias
    """
    cleaned = clean_text(text)
    words = cleaned.split()
    return sum(1 for word in words if word in keywords)


def process_document(doc: Dict, keywords: List[str]) -> Dict:
    """
    Procesa un documento individual.
    
    Args:
        doc (Dict): Documento con campos 'id', 'date', 'text'
        keywords (List[str]): Lista de keywords
        
    Returns:
        Dict: Documento procesado con estadísticas
    """
    try:
        text = doc.get("text", "")
        cleaned_text = clean_text(text)
        
        return {
            "date": doc.get("date"),
            "doc_id": doc.get("id"),
            "keyword_hits": count_keywords(text, keywords),
            "text_length": len(text),
            "word_count": len(cleaned_text.split())
        }
    except Exception as e:
        logger.error(f"Error procesando documento {doc.get('id')}: {e}")
        return None


def process_file_chunk(file_path: str, keywords: List[str]) -> List[Dict]:
    """
    Procesa un archivo completo en chunks.
    
    Args:
        file_path (str): Ruta del archivo JSONL
        keywords (List[str]): Lista de keywords
        
    Returns:
        List[Dict]: Lista de documentos procesados
    """
    results = []
    chunk = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                try:
                    doc = json.loads(line)
                    chunk.append(doc)
                    
                    # Procesar en chunks para eficiencia
                    if len(chunk) >= CHUNK_SIZE:
                        for document in chunk:
                            result = process_document(document, keywords)
                            if result:
                                results.append(result)
                        chunk = []
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Error en línea {i} de {file_path}: {e}")
                    continue
            
            # Procesar chunk final
            if chunk:
                for document in chunk:
                    result = process_document(document, keywords)
                    if result:
                        results.append(result)
        
        logger.info(f"Procesados {len(results)} documentos de {file_path}")
        return results
        
    except Exception as e:
        logger.error(f"Error procesando archivo {file_path}: {e}")
        return []


def process_files_parallel(files: List[str], keywords: List[str], num_workers: int) -> List[Dict]:
    """
    Procesa múltiples archivos en paralelo.
    
    Args:
        files (List[str]): Lista de rutas de archivos
        keywords (List[str]): Lista de keywords
        num_workers (int): Número de workers paralelos
        
    Returns:
        List[Dict]: Todos los resultados combinados
    """
    logger.info(f"Iniciando procesamiento paralelo con {num_workers} workers")
    start_time = time.time()
    
    # Usar partial para pasar keywords a la función
    process_func = partial(process_file_chunk, keywords=keywords)
    
    # Crear pool de workers
    with Pool(processes=num_workers) as pool:
        # Map files to workers
        results_nested = pool.map(process_func, files)
    
    # Flatten results
    all_results = [item for sublist in results_nested for item in sublist]
    
    elapsed_time = time.time() - start_time
    logger.info(f"Procesamiento completado en {elapsed_time:.2f} segundos")
    logger.info(f"Total de documentos procesados: {len(all_results)}")
    logger.info(f"Throughput: {len(all_results)/elapsed_time:.2f} docs/seg")
    
    return all_results


def save_results(results: List[Dict], output_file: str):
    """
    Guarda resultados en CSV.
    
    Args:
        results (List[Dict]): Lista de resultados
        output_file (str): Ruta del archivo de salida
    """
    df = pd.DataFrame(results)
    
    # Ordenar por fecha
    df = df.sort_values('date')
    
    # Guardar
    df.to_csv(output_file, index=False)
    logger.info(f"Resultados guardados en {output_file}")
    
    # Estadísticas
    logger.info(f"Estadísticas:")
    logger.info(f"  - Total documentos: {len(df)}")
    logger.info(f"  - Rango de fechas: {df['date'].min()} a {df['date'].max()}")
    logger.info(f"  - Total keyword hits: {df['keyword_hits'].sum()}")
    logger.info(f"  - Promedio hits por documento: {df['keyword_hits'].mean():.2f}")


def main():
    """
    Función principal de procesamiento paralelo.
    """
    logger.info("=== INICIANDO PROCESSOR PARALELO ===")
    logger.info(f"Workers configurados: {NUM_WORKERS}")
    logger.info(f"Chunk size: {CHUNK_SIZE}")
    
    # Obtener lista de archivos
    files = [
        os.path.join(INPUT_PATH, f)
        for f in os.listdir(INPUT_PATH)
        if f.endswith('.jsonl')
    ]
    
    if not files:
        logger.warning(f"No se encontraron archivos .jsonl en {INPUT_PATH}")
        return
    
    logger.info(f"Archivos a procesar: {len(files)}")
    for f in files:
        logger.info(f"  - {f}")
    
    # Procesar en paralelo
    results = process_files_parallel(files, KEYWORDS, NUM_WORKERS)
    
    if not results:
        logger.error("No se obtuvieron resultados del procesamiento")
        return
    
    # Guardar resultados
    output_file = os.path.join(OUTPUT_PATH, "results.csv")
    save_results(results, output_file)
    
    logger.info("=== PROCESSOR COMPLETADO ===")


if __name__ == "__main__":
    main()
