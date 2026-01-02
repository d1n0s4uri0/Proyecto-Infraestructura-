"""
Módulo de métricas de rendimiento
Recolecta y exporta métricas para Prometheus y análisis
"""

import time
import psutil
import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import threading

logger = logging.getLogger(__name__)


# ==========================================
# MÉTRICAS PROMETHEUS
# ==========================================

# Contadores
documents_processed = Counter(
    'documents_processed_total',
    'Total de documentos procesados',
    ['status']  # success, error
)

files_processed = Counter(
    'files_processed_total',
    'Total de archivos procesados',
    ['status']
)

# Histogramas (tiempos)
processing_time = Histogram(
    'processing_time_seconds',
    'Tiempo de procesamiento de documentos',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

file_processing_time = Histogram(
    'file_processing_time_seconds',
    'Tiempo de procesamiento por archivo',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Gauges (valores actuales)
cpu_usage = Gauge('cpu_usage_percent', 'Uso de CPU')
memory_usage = Gauge('memory_usage_mb', 'Uso de memoria en MB')
active_workers = Gauge('active_workers', 'Número de workers activos')


# ==========================================
# DATACLASSES PARA MÉTRICAS
# ==========================================

@dataclass
class ProcessingMetrics:
    """Métricas de procesamiento de un archivo o batch."""
    file_name: str
    start_time: float
    end_time: float
    duration: float
    documents_count: int
    success_count: int
    error_count: int
    throughput: float  # docs/second
    cpu_usage_avg: float
    memory_usage_mb: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SystemMetrics:
    """Métricas del sistema."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_percent: float
    num_workers: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ==========================================
# CLASE PRINCIPAL DE MÉTRICAS
# ==========================================

class MetricsCollector:
    """
    Recolector de métricas de rendimiento.
    """
    
    def __init__(self, output_dir: str = "data/metrics"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.processing_metrics: List[ProcessingMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        
        # Thread para monitoreo continuo
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: int = 5):
        """
        Inicia monitoreo continuo del sistema.
        
        Args:
            interval (int): Intervalo en segundos
        """
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Monitoreo de sistema iniciado (intervalo: {interval}s)")
    
    def stop_monitoring(self):
        """Detiene el monitoreo."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Monitoreo de sistema detenido")
    
    def _monitor_loop(self, interval: int):
        """Loop interno de monitoreo."""
        while self.monitoring:
            self._collect_system_metrics()
            time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Recolecta métricas del sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_usage.set(cpu_percent)
            
            # Memoria
            mem = psutil.virtual_memory()
            memory_mb = mem.used / (1024 * 1024)
            memory_usage.set(memory_mb)
            
            # Disco
            disk = psutil.disk_usage('/')
            
            # Crear métrica
            metric = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=mem.percent,
                memory_mb=memory_mb,
                disk_usage_percent=disk.percent,
                num_workers=psutil.cpu_count()
            )
            
            self.system_metrics.append(metric)
            
        except Exception as e:
            logger.error(f"Error recolectando métricas del sistema: {e}")
    
    def record_processing(
        self,
        file_name: str,
        start_time: float,
        end_time: float,
        success_count: int,
        error_count: int
    ):
        """
        Registra métricas de procesamiento de un archivo.
        
        Args:
            file_name (str): Nombre del archivo
            start_time (float): Tiempo de inicio
            end_time (float): Tiempo de fin
            success_count (int): Documentos exitosos
            error_count (int): Documentos con error
        """
        duration = end_time - start_time
        total_docs = success_count + error_count
        throughput = total_docs / duration if duration > 0 else 0
        
        # Métricas actuales del sistema
        cpu_percent = psutil.cpu_percent()
        mem_mb = psutil.virtual_memory().used / (1024 * 1024)
        
        # Crear métrica
        metric = ProcessingMetrics(
            file_name=file_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            documents_count=total_docs,
            success_count=success_count,
            error_count=error_count,
            throughput=throughput,
            cpu_usage_avg=cpu_percent,
            memory_usage_mb=mem_mb
        )
        
        self.processing_metrics.append(metric)
        
        # Actualizar métricas Prometheus
        documents_processed.labels(status='success').inc(success_count)
        documents_processed.labels(status='error').inc(error_count)
        files_processed.labels(status='success').inc()
        file_processing_time.observe(duration)
        
        logger.info(f"Métricas registradas para {file_name}: "
                   f"{throughput:.2f} docs/seg, "
                   f"CPU: {cpu_percent:.1f}%, "
                   f"MEM: {mem_mb:.1f}MB")
    
    def save_metrics(self):
        """Guarda métricas en archivos JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar métricas de procesamiento
        if self.processing_metrics:
            processing_file = os.path.join(
                self.output_dir,
                f"processing_metrics_{timestamp}.json"
            )
            with open(processing_file, 'w') as f:
                json.dump(
                    [m.to_dict() for m in self.processing_metrics],
                    f,
                    indent=2
                )
            logger.info(f"Métricas de procesamiento guardadas: {processing_file}")
        
        # Guardar métricas del sistema
        if self.system_metrics:
            system_file = os.path.join(
                self.output_dir,
                f"system_metrics_{timestamp}.json"
            )
            with open(system_file, 'w') as f:
                json.dump(
                    [m.to_dict() for m in self.system_metrics],
                    f,
                    indent=2
                )
            logger.info(f"Métricas del sistema guardadas: {system_file}")
    
    def generate_report(self) -> Dict:
        """
        Genera reporte de métricas agregadas.
        
        Returns:
            Dict: Reporte con estadísticas
        """
        if not self.processing_metrics:
            return {"error": "No hay métricas disponibles"}
        
        # Calcular estadísticas agregadas
        total_docs = sum(m.documents_count for m in self.processing_metrics)
        total_success = sum(m.success_count for m in self.processing_metrics)
        total_errors = sum(m.error_count for m in self.processing_metrics)
        total_duration = sum(m.duration for m in self.processing_metrics)
        
        avg_throughput = sum(m.throughput for m in self.processing_metrics) / len(self.processing_metrics)
        avg_cpu = sum(m.cpu_usage_avg for m in self.processing_metrics) / len(self.processing_metrics)
        avg_memory = sum(m.memory_usage_mb for m in self.processing_metrics) / len(self.processing_metrics)
        
        report = {
            "summary": {
                "total_files_processed": len(self.processing_metrics),
                "total_documents": total_docs,
                "successful_documents": total_success,
                "failed_documents": total_errors,
                "success_rate": (total_success / total_docs * 100) if total_docs > 0 else 0,
                "total_processing_time_seconds": total_duration
            },
            "performance": {
                "average_throughput_docs_per_second": avg_throughput,
                "average_cpu_usage_percent": avg_cpu,
                "average_memory_usage_mb": avg_memory
            },
            "details": [m.to_dict() for m in self.processing_metrics[-10:]]  # Últimos 10
        }
        
        return report
    
    def print_report(self):
        """Imprime reporte en consola."""
        report = self.generate_report()
        
        print("\n" + "="*50)
        print("REPORTE DE MÉTRICAS DE RENDIMIENTO")
        print("="*50)
        
        if "error" in report:
            print(f"ERROR: {report['error']}")
            return
        
        print("\n📊 RESUMEN:")
        for key, value in report["summary"].items():
            print(f"  {key}: {value}")
        
        print("\n⚡ RENDIMIENTO:")
        for key, value in report["performance"].items():
            print(f"  {key}: {value:.2f}")
        
        print("\n" + "="*50 + "\n")


# ==========================================
# FUNCIONES HELPER
# ==========================================

def get_prometheus_metrics() -> bytes:
    """
    Obtiene métricas en formato Prometheus.
    
    Returns:
        bytes: Métricas en formato Prometheus
    """
    return generate_latest(REGISTRY)


# Singleton global
metrics_collector = MetricsCollector()
