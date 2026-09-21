@echo off
chcp 65001 >nul
title Patoruzú Stats

echo.
echo  ==========================================
echo   PATORUZÚ STATS — Iniciando...
echo  ==========================================
echo.

:: ── 1. Buscar Python (en PATH o en rutas típicas de instalación) ──────────
set PYTHON=

:: Primero intentar directamente desde PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :python_found
)

:: Buscar en rutas típicas de Windows (con y sin checkbox de PATH)
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%PROGRAMFILES%\Python313\python.exe"
    "%PROGRAMFILES%\Python312\python.exe"
    "%PROGRAMFILES%\Python311\python.exe"
    "%PROGRAMFILES(X86)%\Python313\python.exe"
    "%PROGRAMFILES(X86)%\Python312\python.exe"
    "%PROGRAMFILES(X86)%\Python311\python.exe"
) do (
    if exist %%p (
        set PYTHON=%%p
        goto :python_found
    )
)

:: Python no encontrado en ningún lado
echo  [ERROR] Python no está instalado.
echo.
echo  Por favor instalarlo desde:
echo  https://www.python.org/downloads/
echo.
echo  Hacer clic en "Download Python" e instalarlo
echo  con todas las opciones por defecto.
echo.
pause
exit /b 1

:python_found
:: Verificar versión mínima 3.11
for /f "tokens=2 delims= " %%v in ('"%PYTHON%" --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)
if %PYMAJOR% LSS 3 goto :version_error
if %PYMAJOR% EQU 3 if %PYMINOR% LSS 11 goto :version_error
echo  [OK] Python %PYVER%
goto :check_port

:version_error
echo  [ERROR] Se requiere Python 3.11 o superior.
echo  Versión instalada: %PYVER%
echo  Descargar desde: https://www.python.org/downloads/
echo.
pause
exit /b 1

:: ── 2. Verificar puerto 8000 libre ────────────────────────────────────────
:check_port
netstat -an 2>nul | find "0.0.0.0:8000" >nul
if not errorlevel 1 (
    echo.
    echo  [AVISO] Patoruzú Stats ya está corriendo.
    echo  Abriendo el navegador...
    echo.
    timeout /t 2 >nul
    start http://localhost:8000
    pause
    exit /b 0
)

:: ── 3. Crear entorno virtual si no existe ─────────────────────────────────
if not exist "venv\" (
    echo  Preparando la app por primera vez, esto tarda un minuto...
    "%PYTHON%" -m venv venv
    if errorlevel 1 (
        echo  [ERROR] No se pudo preparar el entorno de la app.
        pause
        exit /b 1
    )
)

:: ── 4. Activar entorno virtual ────────────────────────────────────────────
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] No se pudo activar el entorno de la app.
    pause
    exit /b 1
)

:: ── 5. Instalar/actualizar dependencias ───────────────────────────────────
echo  Verificando dependencias...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [ERROR] No se pudieron instalar los componentes necesarios.
    echo  Verificar conexión a internet e intentar de nuevo.
    pause
    exit /b 1
)
echo  [OK] Todo listo

:: ── 6. Abrir navegador y arrancar servidor ────────────────────────────────
echo.
echo  Iniciando Patoruzú Stats...
echo  Para cerrar la app, cerrá esta ventana.
echo.
timeout /t 2 >nul
start http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port 8000

pause
