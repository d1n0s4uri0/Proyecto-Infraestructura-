@echo off
REM Script para construir y gestionar contenedores Docker en Windows
REM Persona A - Proyecto Infraestructuras

setlocal enabledelayedexpansion

REM Variables
set PROJECT_NAME=news-analysis
set REGISTRY=your-registry.io
set VERSION=1.0.0

REM Colores para Windows (usando echo con colores ANSI)
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set NC=[0m

REM Mostrar ayuda
if "%1"=="" goto :show_help
if "%1"=="help" goto :show_help
if "%1"=="build" goto :build_images
if "%1"=="push" goto :push_images
if "%1"=="run" goto :run_services
if "%1"=="stop" goto :stop_services
if "%1"=="clean" goto :clean_all
if "%1"=="logs" goto :show_logs
if "%1"=="test" goto :test_services
goto :show_help

:show_help
echo.
echo Uso: build.bat [COMANDO]
echo.
echo Comandos disponibles:
echo   build       - Construir todas las imagenes
echo   push        - Subir imagenes al registry
echo   run         - Ejecutar con docker-compose
echo   stop        - Detener contenedores
echo   clean       - Limpiar contenedores e imagenes
echo   logs        - Ver logs de los servicios
echo   test        - Probar los servicios
echo.
exit /b 0

:build_images
echo %GREEN%[*] Construyendo imagenes Docker...%NC%
echo.
echo Construyendo acquirer...
docker build -t %PROJECT_NAME%-acquirer:%VERSION% -f data_acquirer.Dockerfile .
if %errorlevel% neq 0 (
    echo %RED%[!] Error construyendo acquirer%NC%
    exit /b 1
)

echo.
echo Construyendo processor...
docker build -t %PROJECT_NAME%-processor:%VERSION% -f processor.Dockerfile .
if %errorlevel% neq 0 (
    echo %RED%[!] Error construyendo processor%NC%
    exit /b 1
)

echo.
echo Construyendo analyzer...
docker build -t %PROJECT_NAME%-analyzer:%VERSION% -f analyzer.Dockerfile .
if %errorlevel% neq 0 (
    echo %RED%[!] Error construyendo analyzer%NC%
    exit /b 1
)

echo.
echo %GREEN%[OK] Imagenes construidas exitosamente%NC%
exit /b 0

:push_images
echo %GREEN%[*] Subiendo imagenes al registry...%NC%

docker tag %PROJECT_NAME%-acquirer:%VERSION% %REGISTRY%/%PROJECT_NAME%-acquirer:%VERSION%
docker tag %PROJECT_NAME%-processor:%VERSION% %REGISTRY%/%PROJECT_NAME%-processor:%VERSION%
docker tag %PROJECT_NAME%-analyzer:%VERSION% %REGISTRY%/%PROJECT_NAME%-analyzer:%VERSION%

docker push %REGISTRY%/%PROJECT_NAME%-acquirer:%VERSION%
docker push %REGISTRY%/%PROJECT_NAME%-processor:%VERSION%
docker push %REGISTRY%/%PROJECT_NAME%-analyzer:%VERSION%

echo %GREEN%[OK] Imagenes subidas exitosamente%NC%
exit /b 0

:run_services
echo %GREEN%[*] Iniciando servicios...%NC%
docker-compose up -d
if %errorlevel% neq 0 (
    echo %RED%[!] Error iniciando servicios%NC%
    exit /b 1
)

echo %GREEN%[OK] Servicios iniciados%NC%
echo.
echo API disponible en: http://localhost:8000
echo Documentacion API: http://localhost:8000/docs
echo Prometheus: http://localhost:9090
echo Grafana: http://localhost:3000 (admin/admin)
exit /b 0

:stop_services
echo %YELLOW%[*] Deteniendo servicios...%NC%
docker-compose down
echo %GREEN%[OK] Servicios detenidos%NC%
exit /b 0

:clean_all
echo %RED%[*] Limpiando contenedores e imagenes...%NC%
set /p confirm="¿Estas seguro? (S/N): "
if /i not "%confirm%"=="S" (
    echo Cancelado
    exit /b 0
)

docker-compose down -v
docker rmi %PROJECT_NAME%-acquirer:%VERSION% 2>nul
docker rmi %PROJECT_NAME%-processor:%VERSION% 2>nul
docker rmi %PROJECT_NAME%-analyzer:%VERSION% 2>nul
echo %GREEN%[OK] Limpieza completada%NC%
exit /b 0

:show_logs
echo %GREEN%[*] Mostrando logs...%NC%
docker-compose logs -f
exit /b 0

:test_services
echo %GREEN%[*] Probando servicios...%NC%
echo.
echo Esperando a que la API inicie...
timeout /t 5 /nobreak >nul

echo Testing /v1/health...
curl -s http://localhost:8000/v1/health
echo.

echo Testing /v1/metrics...
curl -s http://localhost:8000/v1/metrics
echo.

echo %GREEN%[OK] Tests completados%NC%
exit /b 0
