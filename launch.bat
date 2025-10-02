@echo off
echo ========================================
echo Decoupeur Video Intelligent - v1.0
echo ========================================
echo.

REM Activer l'environnement virtuel
call venv_312\Scripts\activate.bat

REM Lancer l'application
echo Lancement de l'application...
python src\main.py

REM Si erreur, attendre avant de fermer
if errorlevel 1 (
    echo.
    echo Une erreur s'est produite.
    echo Consultez les logs dans le dossier logs/
    pause
)
