@echo off
REM Script para desplegar en Kubernetes
REM Persona A - Proyecto Infraestructuras

setlocal enabledelayedexpansion

REM Colores
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set NC=[0m

REM Mostrar ayuda
if "%1"=="" goto :show_help
if "%1"=="help" goto :show_help
if "%1"=="deploy" goto :deploy_all
if "%1"=="delete" goto :delete_all
if "%1"=="status" goto :show_status
if "%1"=="logs" goto :show_logs
if "%1"=="test" goto :test_api
if "%1"=="scale" goto :scale_deployment
if "%1"=="update" goto :update_deployments
if "%1"=="run-acquirer" goto :run_acquirer
if "%1"=="run-colcap" goto :run_colcap
goto :show_help

:show_help
echo.
echo Uso: deploy-k8s.bat [COMANDO] [ARGUMENTOS]
echo.
echo Comandos disponibles:
echo   deploy          - Desplegar todos los recursos
echo   delete          - Eliminar todos los recursos
echo   status          - Ver estado de recursos
echo   logs [app]      - Ver logs (acquirer, processor, analyzer)
echo   test            - Probar API
echo   scale [n]       - Escalar replicas del analyzer
echo   update          - Actualizar deployments
echo   run-acquirer    - Ejecutar scraper manualmente
echo   run-colcap      - Actualizar datos COLCAP manualmente
echo.
exit /b 0

:deploy_all
echo %GREEN%[*] Desplegando recursos en Kubernetes...%NC%
echo.

echo Creando namespace...
kubectl apply -f k8s/00-namespace.yaml

echo Creando ConfigMap...
kubectl apply -f k8s/01-configmap.yaml

echo Creando PVC...
kubectl apply -f k8s/02-pvc.yaml

echo Desplegando Processor...
kubectl apply -f k8s/03-processor-deployment.yaml

echo Desplegando Analyzer...
kubectl apply -f k8s/04-analyzer-deployment.yaml

echo Creando Service...
kubectl apply -f k8s/05-analyzer-service.yaml

echo Configurando HPA...
kubectl apply -f k8s/06-hpa.yaml

echo Configurando Processor Job...
kubectl apply -f k8s/07-processor-job.yaml

echo Configurando Processor CronJob...
kubectl apply -f k8s/08-processor-cronjob.yaml

echo Configurando Acquirer CronJob...
kubectl apply -f k8s/09-acquirer-cronjob.yaml

echo Configurando COLCAP Updater CronJob...
kubectl apply -f k8s/11-colcap-cronjob.yaml

echo.
echo %YELLOW%[*] Esperando a que los pods esten listos...%NC%
kubectl wait --for=condition=ready pod -l app=analyzer -n news-analysis --timeout=300s 2>nul

echo.
echo %GREEN%[OK] Recursos desplegados exitosamente%NC%
echo.
echo Para obtener la IP del servicio:
echo kubectl get service analyzer-service -n news-analysis
echo.
exit /b 0

:delete_all
echo %RED%[*] Eliminando recursos...%NC%
set /p confirm="¿Estas seguro? (S/N): "
if /i not "%confirm%"=="S" (
    echo Cancelado
    exit /b 0
)

kubectl delete -f k8s/09-acquirer-cronjob.yaml 2>nul
kubectl delete -f k8s/08-processor-cronjob.yaml 2>nul
kubectl delete -f k8s/07-processor-job.yaml 2>nul
kubectl delete -f k8s/06-hpa.yaml 2>nul
kubectl delete -f k8s/05-analyzer-service.yaml 2>nul
kubectl delete -f k8s/04-analyzer-deployment.yaml 2>nul
kubectl delete -f k8s/03-processor-deployment.yaml 2>nul
kubectl delete -f k8s/02-pvc.yaml 2>nul
kubectl delete -f k8s/01-configmap.yaml 2>nul
kubectl delete -f k8s/00-namespace.yaml 2>nul

echo %GREEN%[OK] Recursos eliminados%NC%
exit /b 0

:show_status
echo %GREEN%[*] Estado de los recursos...%NC%
echo.

echo Pods:
kubectl get pods -n news-analysis

echo.
echo Services:
kubectl get services -n news-analysis

echo.
echo HPA:
kubectl get hpa -n news-analysis

echo.
echo CronJobs:
kubectl get cronjobs -n news-analysis

echo.
exit /b 0

:show_logs
if "%2"=="" (
    echo %RED%[!] Especifica la aplicacion: acquirer, processor o analyzer%NC%
    echo Uso: deploy-k8s.bat logs [app]
    exit /b 1
)

echo %GREEN%[*] Mostrando logs de %2...%NC%
kubectl logs -l app=%2 -n news-analysis --tail=100 -f
exit /b 0

:test_api
echo %GREEN%[*] Probando API en Kubernetes...%NC%
echo.

for /f "tokens=*" %%i in ('kubectl get service analyzer-service -n news-analysis -o jsonpath^="{.status.loadBalancer.ingress[0].ip}" 2^>nul') do set EXTERNAL_IP=%%i

if "!EXTERNAL_IP!"=="" (
    echo %YELLOW%[WARN] Service aun no tiene EXTERNAL-IP%NC%
    echo Intentando con NodePort...
    for /f "tokens=*" %%i in ('kubectl get nodes -o jsonpath^="{.items[0].status.addresses[?^(@.type^=^=^\"ExternalIP^\"^)].address}" 2^>nul') do set NODE_IP=%%i
    for /f "tokens=*" %%i in ('kubectl get service analyzer-service -n news-analysis -o jsonpath^="{.spec.ports[0].nodePort}" 2^>nul') do set NODE_PORT=%%i
    set API_URL=http://!NODE_IP!:!NODE_PORT!
) else (
    set API_URL=http://!EXTERNAL_IP!
)

echo Testing: !API_URL!/v1/health
curl -s !API_URL!/v1/health
echo.
exit /b 0

:scale_deployment
if "%2"=="" (
    echo %RED%[!] Especifica el numero de replicas%NC%
    echo Uso: deploy-k8s.bat scale [numero]
    exit /b 1
)

echo %GREEN%[*] Escalando analyzer a %2 replicas...%NC%
kubectl scale deployment analyzer-deployment --replicas=%2 -n news-analysis

echo %GREEN%[OK] Escalado a %2 replicas%NC%
exit /b 0

:update_deployments
echo %GREEN%[*] Actualizando deployments...%NC%

kubectl rollout restart deployment analyzer-deployment -n news-analysis
kubectl rollout restart deployment processor-deployment -n news-analysis

echo %GREEN%[OK] Deployments actualizados%NC%
exit /b 0

:run_acquirer
echo %GREEN%[*] Ejecutando Acquirer Job manualmente...%NC%

kubectl delete job acquirer-job -n news-analysis 2>nul
kubectl apply -f k8s/10-acquirer-job.yaml

echo.
echo %GREEN%[OK] Job creado. Ver progreso con:%NC%
echo kubectl logs -f job/acquirer-job -n news-analysis
echo.
exit /b 0

:run_colcap
echo %GREEN%[*] Ejecutando COLCAP Job manualmente...%NC%

kubectl delete job colcap-job -n news-analysis 2>nul
kubectl apply -f k8s/12-colcap-job.yaml

echo.
echo %GREEN%[OK] Job creado. Ver progreso con:%NC%
echo kubectl logs -f job/colcap-job -n news-analysis
echo.
exit /b 0
