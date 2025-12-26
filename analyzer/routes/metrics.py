from fastapi import APIRouter
import os
from analyzer.schemas import MetricResponse

router = APIRouter(prefix="/v1", tags=["Metrics"])

BASE_PATH = "data/aggregated"

@router.get(
    "/metrics",
    response_model=MetricResponse,
    summary="Métricas de correlación",
    description="Devuelve la correlación entre la actividad noticiosa y el índice COLCAP"
)
def get_metrics():
    metrics_file = os.path.join(BASE_PATH, "metrics.txt")

    if not os.path.exists(metrics_file):
        return MetricResponse(
            descripcion="No hay métricas disponibles",
            valores=""
        )

    with open(metrics_file, "r") as f:
        contenido = f.read()

    return MetricResponse(
        descripcion="Correlaciones calculadas",
        valores=contenido
    )

