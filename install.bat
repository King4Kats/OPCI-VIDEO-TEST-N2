@echo off
echo ========================================
echo Installation du Decoupeur Video Intelligent
echo ========================================
echo.

REM Verification de Python
echo [1/5] Verification de Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERREUR: Python n'est pas installe ou non accessible
    echo Telechargez Python 3.12 sur: https://python.org
    pause
    exit /b 1
)
python --version

REM Verification de FFmpeg
echo.
echo [2/5] Verification de FFmpeg...
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo AVERTISSEMENT: FFmpeg n'est pas installe ou non accessible
    echo Telechargez FFmpeg sur: https://www.gyan.dev/ffmpeg/builds/
    echo L'application ne fonctionnera pas sans FFmpeg !
    pause
) else (
    echo FFmpeg detecte !
)

REM Verification d'Ollama
echo.
echo [3/5] Verification d'Ollama...
ollama --version >nul 2>&1
if %errorLevel% neq 0 (
    echo AVERTISSEMENT: Ollama n'est pas installe
    echo Telechargez Ollama sur: https://ollama.ai/download
    echo L'analyse IA ne fonctionnera pas sans Ollama !
    pause
) else (
    echo Ollama detecte !
)

REM Creation de l'environnement virtuel si necessaire
echo.
echo [4/5] Configuration de l'environnement virtuel...
if not exist "venv_312\Scripts\activate.bat" (
    echo Creation de l'environnement virtuel...
    python -m venv venv_312
    if %errorLevel% neq 0 (
        echo ERREUR: Impossible de creer l'environnement virtuel
        pause
        exit /b 1
    )
) else (
    echo Environnement virtuel deja present.
)

REM Activation et installation des dependances
echo.
echo [5/5] Installation des dependances Python...
echo Cela peut prendre 10-30 minutes (telechargement de ~3 GB)...
call venv_312\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorLevel% neq 0 (
    echo.
    echo ERREUR: L'installation des dependances a echoue
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation terminee avec succes !
echo ========================================
echo.
echo Pour lancer l'application, double-cliquez sur: launch.bat
echo.
pause
