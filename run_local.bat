@echo off
REM RedFlag-AI - Lancement local (sans Docker)

echo ============================================
echo   RedFlag-AI - Lancement LOCAL
echo ============================================
echo.

cd /d "%~dp0"

REM Verification des fichiers necessaires
echo [1/4] Verification des fichiers...

if not exist "data\raw\patients_synthetic.csv" (
    echo       Generation du dataset...
    python scripts\generate_dataset.py --n_samples 1000 --output data\raw\patients_synthetic.csv
) else (
    echo       Dataset OK
)

if not exist "models\trained\triage_model.json" (
    echo       Entrainement du modele ML...
    python scripts\train_model.py --data data\raw\patients_synthetic.csv --output models\trained
) else (
    echo       Modele ML OK
)

if not exist "data\vector_store\medical_kb.faiss" (
    echo       Construction de la base de connaissances...
    python scripts\build_knowledge_base.py --input docs\medical_knowledge.md --output data\vector_store\medical_kb
) else (
    echo       Base de connaissances OK
)

echo.
echo [2/4] Configuration PYTHONPATH...
set PYTHONPATH=%CD%

echo.
echo [3/4] Demarrage de Streamlit...
echo.
echo ============================================
echo   Interface disponible sur :
echo   http://localhost:8501
echo ============================================
echo.

streamlit run src\interface\app.py --server.port 8501
