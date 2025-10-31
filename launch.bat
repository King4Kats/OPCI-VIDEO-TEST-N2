@echo off
echo ========================================
echo Decoupeur Video Intelligent - v1.0
echo ========================================
echo.

REM Verification de l'environnement virtuel
if not exist "venv_312\Scripts\activate.bat" (
    echo ERREUR: L'environnement virtuel n'existe pas.
    echo Veuillez d'abord creer l'environnement avec:
    echo   python -m venv venv_312
    echo   venv_312\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
call venv_312\Scripts\activate.bat

REM Verification que src\main.py existe
if not exist "src\main.py" (
    echo ERREUR: Le fichier src\main.py n'existe pas.
    echo Verifiez que vous etes dans le bon dossier.
    pause
    exit /b 1
)

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
