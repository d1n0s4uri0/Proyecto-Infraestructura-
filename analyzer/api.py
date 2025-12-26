from fastapi import FastAPI
from analyzer.routes import metrics, daily, plots

app = FastAPI(
    title="Plataforma de Análisis de Noticias",
    version="1.0",
    description="API para consultar resultados del análisis distribuido de noticias"
)

# Registro de rutas
app.include_router(metrics.router)
app.include_router(daily.router)
app.include_router(plots.router)

@app.get(
    "/",
    summary="Estado general de la plataforma",
    description="Endpoint principal de la plataforma de análisis"
)
def root():
    return {
        "platform": "Plataforma de Análisis de Noticias",
        "version": "1.0",
        "status": "running"
    }
