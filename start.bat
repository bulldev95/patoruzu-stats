@echo off
chcp 65001 >nul
title Patoruzú Stats

echo.
echo  ==========================================
echo   PATORUZÚ STATS — Iniciando...
echo  ==========================================
echo.

:: ── 1. Verificar Python ───────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no está instalado.
    echo.
    echo  Por favor instalarlo desde:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: durante la instalación marcar la opción
    echo  "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: Verificar versión mínima 3.11
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)
if %PYMAJOR% LSS 3 (
    echo  [ERROR] Se requiere Python 3.11 o superior.
    echo  Versión instalada: %PYVER%
    echo  Descargar desde: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
if %PYMAJOR% EQU 3 if %PYMINOR% LSS 11 (
    echo  [ERROR] Se requiere Python 3.11 o superior.
    echo  Versión instalada: %PYVER%
    echo  Descargar desde: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo  [OK] Python %PYVER%

:: ── 2. Verificar puerto 8000 libre ────────────────────────────────────────
netstat -an 2>nul | find "0.0.0.0:8000" >nul
if not errorlevel 1 (
    echo.
    echo  [AVISO] El puerto 8000 ya está en uso.
    echo  Puede que Patoruzú Stats ya esté corriendo.
    echo  Abriendo el navegador...
    echo.
    timeout /t 2 >nul
    start http://localhost:8000
    pause
    exit /b 0
)

:: ── 3. Crear entorno virtual si no existe ─────────────────────────────────
if not exist "venv\" (
    echo  Creando entorno virtual por primera vez...
    python -m venv venv
    if errorlevel 1 (
        echo  [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo  [OK] Entorno virtual creado
)

:: ── 4. Activar entorno virtual ────────────────────────────────────────────
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

:: ── 5. Instalar/actualizar dependencias ───────────────────────────────────
echo  Verificando dependencias...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [ERROR] No se pudieron instalar las dependencias.
    echo  Verificar conexión a internet e intentar de nuevo.
    pause
    exit /b 1
)
echo  [OK] Dependencias listas

:: ── 6. Abrir navegador y arrancar servidor ────────────────────────────────
echo.
echo  Iniciando servidor...
echo  Para cerrar la app, cerrá esta ventana.
echo.
timeout /t 2 >nul
start http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port 8000

pause
