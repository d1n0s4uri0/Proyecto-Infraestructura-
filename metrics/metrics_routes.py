"""
Ruta de métricas para FastAPI
Expone métricas de Prometheus
"""

from fastapi import APIRouter, Response
from metrics.metrics_collector import get_prometheus_metrics, metrics_collector

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get(
    "",
    summary="Métricas de Prometheus",
    description="Endpoint para recolección de métricas por Prometheus"
)
def prometheus_metrics():
    """
    Expone métricas en formato Prometheus.
    """
    metrics = get_prometheus_metrics()
    return Response(
        content=metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get(
    "/report",
    summary="Reporte de métricas",
    description="Obtiene reporte detallado de métricas de rendimiento"
)
def get_metrics_report():
    """
    Obtiene reporte de métricas de rendimiento.
    """
    return metrics_collector.generate_report()
