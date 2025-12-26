from fastapi import APIRouter
import os
from analyzer.schemas import HealthResponse, PlotsResponse

router = APIRouter(prefix="/v1", tags=["Plots"])

PLOTS_PATH = "data/aggregated/plots"

@router.get(
    "/plots",
    response_model=PlotsResponse,
    summary="Listar gráficas disponibles",
    description="Devuelve las visualizaciones generadas por el sistema"
)
def list_plots():
    if not os.path.exists(PLOTS_PATH):
        return PlotsResponse(
            descripcion="No hay gráficas disponibles",
            plots=[]
        )

    return PlotsResponse(
        descripcion="Gráficas generadas",
        plots=os.listdir(PLOTS_PATH)
    )

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Estado del sistema",
    description="Endpoint de verificación del estado de la plataforma"
)
def health_check():
    return HealthResponse(
        status="OK",
        processor="activo",
        analyzer="activo",
        api="activo"
    )
