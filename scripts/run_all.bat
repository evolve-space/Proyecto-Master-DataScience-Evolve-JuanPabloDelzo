@echo off
setlocal enabledelayedexpansion

REM Cambia al directorio donde esta este archivo .bat
cd /d "%~dp0"

set EXIT_CODE=0

for %%f in (1.*.py 2.*.py 3.*.py 4.*.py) do (
    echo.
    echo ========================================
    echo Ejecutando %%f
    echo ========================================
    python "%%f"
    if errorlevel 1 (
        echo ERROR: %%f termino con codigo %errorlevel%
        set EXIT_CODE=1
        goto :end
    )
)

:end
if %EXIT_CODE%==0 (
    echo.
    echo Todos los programas corrieron correctamente.
) else (
    echo.
    echo Se detuvo la ejecucion por un error.
)

exit /b %EXIT_CODE%
