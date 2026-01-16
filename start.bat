@echo off
REM RedFlag-AI - Script de demarrage (Windows)

echo ============================================
echo   RedFlag-AI - Demarrage de l'application
echo ============================================
echo.

REM Verification de Docker
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [X] Docker n'est pas installe.
    echo     Installez Docker Desktop : https://docs.docker.com/desktop/install/windows/
    pause
    exit /b 1
)

echo [OK] Docker detecte
echo.

REM Construction et demarrage
echo [1/2] Construction des images Docker...
docker compose build

echo.
echo [2/2] Demarrage des services...
docker compose up -d

echo.
echo ============================================
echo   [OK] Application demarree avec succes!
echo ============================================
echo.
echo   Interface Streamlit : http://localhost:8501
echo.
echo   Commandes utiles :
echo      - Voir les logs    : docker compose logs -f
echo      - Arreter          : docker compose down
echo      - Triage CLI       : docker compose run --rm cli
echo.
pause
