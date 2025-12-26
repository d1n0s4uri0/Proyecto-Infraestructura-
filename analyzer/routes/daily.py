from fastapi import APIRouter
import pandas as pd
import os
from analyzer.schemas import DailyResponse

router = APIRouter(prefix="/v1", tags=["Daily Analysis"])

BASE_PATH = "data/aggregated"

@router.get(
    "/daily",
    response_model=DailyResponse,
    summary="Datos agregados por día",
    description="Devuelve los resultados diarios del análisis de noticias"
)
def get_daily_data():
    csv_path = os.path.join(BASE_PATH, "merged_daily.csv")

    if not os.path.exists(csv_path):
        return DailyResponse(
            descripcion="No hay datos agregados",
            data=[]
        )

    df = pd.read_csv(csv_path)

    return DailyResponse(
        descripcion="Resultados diarios del análisis",
        data=df.to_dict(orient="records")
    )

