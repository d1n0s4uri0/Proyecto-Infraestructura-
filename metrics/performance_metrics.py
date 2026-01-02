"""
Performance Metrics Collector
Recolecta métricas de desempeño del sistema
"""

import time
import psutil
import json
import os
from datetime import datetime
from typing import Dict, Any

class PerformanceMetrics:
    """Recolector de métricas de desempeño"""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {
            'execution_times': {},
            'resource_usage': {},
            'parallelism': {},
            'system_info': self._get_system_info()
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema"""
        return {
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'platform': os.uname().sysname,
            'python_version': os.sys.version.split()[0]
        }
    
    def start_timer(self, task_name: str):
        """Inicia timer para una tarea"""
        self.start_time = time.time()
        self.metrics['execution_times'][task_name] = {
            'start': datetime.now().isoformat(),
            'start_timestamp': self.start_time
        }
    
    def end_timer(self, task_name: str):
        """Finaliza timer para una tarea"""
        if task_name not in self.metrics['execution_times']:
            return
        
        end_time = time.time()
        elapsed = end_time - self.metrics['execution_times'][task_name]['start_timestamp']
        
        self.metrics['execution_times'][task_name].update({
            'end': datetime.now().isoformat(),
            'elapsed_seconds': round(elapsed, 2),
            'elapsed_formatted': self._format_time(elapsed)
        })
    
    def record_resource_usage(self, task_name: str):
        """Registra uso de recursos"""
        self.metrics['resource_usage'][task_name] = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def record_parallelism_metrics(self, 
                                   workers: int, 
                                   items_processed: int,
                                   execution_time: float):
        """Registra métricas de paralelismo"""
        throughput = items_processed / execution_time if execution_time > 0 else 0
        
        self.metrics['parallelism'] = {
            'workers': workers,
            'items_processed': items_processed,
            'execution_time': execution_time,
            'throughput_items_per_sec': round(throughput, 2),
            'speedup_theoretical': workers,
            'efficiency_percent': round((throughput / workers) * 100, 2) if workers > 0 else 0
        }
    
    def _format_time(self, seconds: float) -> str:
        """Formatea tiempo en formato legible"""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}m {secs:.2f}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {mins}m {secs:.2f}s"
    
    def save_metrics(self, output_path: str = "data/metrics/performance_metrics.json"):
        """Guarda métricas en archivo JSON"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"✅ Métricas guardadas en: {output_path}")
    
    def print_summary(self):
        """Imprime resumen de métricas"""
        print("\n" + "=" * 70)
        print("RESUMEN DE MÉTRICAS DE DESEMPEÑO")
        print("=" * 70)
        
        # Sistema
        print("\n📊 INFORMACIÓN DEL SISTEMA:")
        for key, value in self.metrics['system_info'].items():
            print(f"  {key}: {value}")
        
        # Tiempos de ejecución
        print("\n⏱️  TIEMPOS DE EJECUCIÓN:")
        for task, data in self.metrics['execution_times'].items():
            if 'elapsed_formatted' in data:
                print(f"  {task}: {data['elapsed_formatted']}")
        
        # Uso de recursos
        print("\n💾 USO DE RECURSOS:")
        for task, data in self.metrics['resource_usage'].items():
            print(f"  {task}:")
            print(f"    CPU: {data['cpu_percent']}%")
            print(f"    Memoria: {data['memory_percent']}% ({data['memory_used_gb']} GB)")
        
        # Paralelismo
        if self.metrics['parallelism']:
            print("\n🚀 MÉTRICAS DE PARALELISMO:")
            p = self.metrics['parallelism']
            print(f"  Workers: {p['workers']}")
            print(f"  Items procesados: {p['items_processed']}")
            print(f"  Throughput: {p['throughput_items_per_sec']} items/seg")
            print(f"  Eficiencia: {p['efficiency_percent']}%")
        
        print("=" * 70)

# Uso en el código existente
"""
# En processor/main.py:

from performance_metrics import PerformanceMetrics

def main():
    metrics = PerformanceMetrics()
    
    # Iniciar timer
    metrics.start_timer('total_processing')
    
    # Tu código de procesamiento
    results = process_files_parallel(files, KEYWORDS, NUM_WORKERS)
    
    # Finalizar timer
    metrics.end_timer('total_processing')
    
    # Registrar recursos
    metrics.record_resource_usage('processing_complete')
    
    # Registrar paralelismo
    metrics.record_parallelism_metrics(
        workers=NUM_WORKERS,
        items_processed=len(results),
        execution_time=metrics.metrics['execution_times']['total_processing']['elapsed_seconds']
    )
    
    # Guardar y mostrar
    metrics.save_metrics()
    metrics.print_summary()
"""
