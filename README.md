## Plataforma de Análisis de Noticias Económica

### Objetivo
Desarrollar un prototipo funcional de software distribuido que procesa y analiza información noticiosa de portales nacionales, correlacionándola con el índice COLCAP (Índice de la Bolsa de Valores de Colombia).

### 1.2 Tecnologías Utilizadas
- **Contenedores**: Docker, Docker Compose
- **Orquestación**: Kubernetes (GKE)
- **Lenguaje**: Python 3.11
- **Frameworks**: FastAPI, pandas, matplotlib
- **Procesamiento Paralelo**: multiprocessing

### Logros Principales
- ✅ Sistema distribuido con 3 microservicios
- ✅ Procesamiento paralelo con 4 workers
- ✅ Actualización automática de datos (CronJobs)
- ✅ API REST para consulta de resultados
- ✅ Despliegue escalable en Kubernetes

## Arquitectura del Sistema

### Diagrama de Arquitectura
```
┌─────────────────────────────────────────────────────────────────┐
│                        KUBERNETES CLUSTER                       │
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐    │
│  │ Data Acquirer  │  │   Processor    │  │    Analyzer     │    │
│  │   (CronJob)    │─▶│     (job)     │─▶│      (job)      │    │
│  │                │  │                │  │                 │    │
│  │ • RSS Scraper  │  │ • Multiprocess │  │ • Correlations  │    │
│  │ • COLCAP Fetch │  │ • 4 Workers    │  │ • API REST      │    │
│  └────────────────┘  └────────────────┘  └─────────────────┘    │
│         │                    │                      │           │
│         └────────────────────┴──────────────────────┘           │
│                              │                                  │
│                    ┌─────────▼─────────┐                        │
│                    │ Persistent Volume  │                       │
│                    │   (Shared Data)    │                       │
│                    └────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                        ┌──────────┐
                        │ Usuarios │
                        │   API    │
                        └──────────┘
```
### Flujo de Datos
```
1. ADQUISICIÓN
   ├─ RSS Scraper → Descarga noticias (últimos 7 días)
   └─ COLCAP Fetcher → Descarga datos bursátiles (últimos 30 días)
   
2. ALMACENAMIENTO
   └─ data/raw/noticias_*.jsonl
   └─ data/indicators/COLCAP.csv
   
3. PROCESAMIENTO (Paralelo)
   ├─ Normalización de texto
   ├─ Detección de keywords económicas
   └─ Agregación por fecha
   
4. ANÁLISIS
   ├─ Fusión con datos COLCAP
   ├─ Cálculo de correlaciones
   └─ Generación de gráficas
   
5. EXPOSICIÓN
   └─ API REST (FastAPI)
      ├─ /v1/health
      ├─ /v1/metrics
      ├─ /v1/daily
      └─ /v1/plots
```
## Componentes del Sistema

### Data Acquirer

**Función**: Descarga automática de datos

**Fuentes**:
- Portafolio.co (RSS)
- La República.co (RSS)
- Banco de la República (RSS)
- Yahoo Finance (COLCAP)

**Tecnologías**:
- feedparser: Parseo de RSS
- requests: HTTP requests
- pandas: Manejo de datos

**Ejecución**:
- CronJob: Diariamente a las 2 AM y 7 PM
- Job manual: Bajo demanda

### Processor

**Función**: Procesamiento paralelo de noticias

**Características**:
- **Paralelismo**: multiprocessing.Pool
- **Workers**: 4 (configurable)
- **Chunk size**: 500 documentos
- **Keywords**: 25 términos económicos

**Algoritmo**:
```python
1. Leer archivos JSONL
2. Dividir en chunks
3. Distribuir a workers
4. Por cada documento:
   a. Normalizar texto (unidecode, lowercase)
   b. Contar keywords económicas
   c. Calcular estadísticas
5. Agregar resultados
6. Guardar CSV
```

### Analyzer

**Función**: Análisis y correlación de datos

**Funcionalidades**:
- Agregación diaria de noticias
- Fusión con datos COLCAP
- Cálculo de correlaciones
- Generación de gráficas
- API REST

**Endpoints**:
```
GET /              → Estado general
GET /v1/health     → Health check
GET /v1/metrics    → Correlaciones calculadas
GET /v1/daily      → Datos diarios agregados
GET /v1/plots      → Lista de gráficas
```

**Correlaciones Calculadas**:
- Keywords vs COLCAP Close
- Documentos por día vs COLCAP Close

---

## Pipeline de Procesamiento

### Adquisición de Datos

**Input**: URLs de RSS, símbolo bursátil  
**Output**: Archivos JSONL, CSV   

**Formato de salida**:
```json
{
  "id": "1",
  "date": "2026-01-01",
  "text": "Noticia completa...",
  "source": "larepublica.co",
  "url": "https://..."
}
```

### Procesamiento Paralelo

**Input**: data/raw/*.jsonl  
**Output**: data/processed/results.csv   

**Algoritmo de paralelización**:
```python
Pool de Workers (4)
├─ Worker 1 
├─ Worker 2
├─ Worker 3
└─ Worker 4
```

Cada worker:
1. Lee chunk de documentos
2. Procesa independientemente
3. Retorna resultados

Coordinador:
1. Distribuye trabajo
2. Recolecta resultados
3. Combina outputs

## Despliegue en Kubernetes

### Recursos Desplegados

```yaml
Namespace: news-analysis

ConfigMaps: 1
PersistentVolumeClaims: 2 (10Gi)

Deployments:
├─ processor-deployment (1 réplicas)
└─ analyzer-deployment (2 réplicas)

Services:
└─ analyzer-service (LoadBalancer)

CronJobs:
├─ acquirer-cronjob (diario 2 AM)
└─ colcap-updater (diario 7 PM)

HorizontalPodAutoscaler:
└─ analyzer-hpa (min: 2, max: 10)

Jobs (manuales):
├─ acquirer-job
├─ processor-job
└─ colcap-job
```

## Resultados y Análisis

### Correlaciones Encontradas

**Interpretación**:
- Correlación positiva débil-moderada
- Mayor actividad noticiosa se asocia levemente con índices bursátiles más altos

### Gráficas Generadas

1. **Keywords por día**: Muestra actividad noticiosa diaria
2. **COLCAP por día**: Evolución del índice bursátil
3. **Keywords vs COLCAP**: Scatter plot de correlación

## Conclusiones

### Logros Técnicos

1.  **Arquitectura Distribuida**: Sistema modular con separación clara de responsabilidades
2.  **Procesamiento Paralelo**: con 4 workers
3.  **Orquestación Efectiva**: Despliegue exitoso en Kubernetes con HPA funcional
4.  **Automatización**: CronJobs para actualización sin intervención manual
5.  **API Funcional**: Exposición de resultados vía REST API

### Desafíos Enfrentados

1. **Configuración de Python Path**: Resuelto con PYTHONPATH y módulos apropiados
2. **Sincronización de Datos**: Uso de PVC para compartir datos entre pods
3. **Detección de Keywords**: Normalización de texto crucial para accuracy

### Aprendizajes

1. Importancia de la modularización en sistemas distribuidos
2. Trade-offs entre paralelismo y overhead de coordinación
3. Configuración apropiada de recursos en Kubernetes
4. Monitoreo y observabilidad en ambientes cloud
