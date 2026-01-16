@echo off
REM RedFlag-AI - Script d'arret (Windows)

echo ============================================
echo   RedFlag-AI - Arret de l'application
echo ============================================
echo.

docker compose down

echo.
echo [OK] Application arretee.
echo.
pause
