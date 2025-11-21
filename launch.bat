@echo off
echo ========================================
echo Decoupeur Video Intelligent - v1.0
echo ========================================
echo.

REM Demander si on doit nettoyer le cache
set /P CLEAN_CACHE="Nettoyer le cache des transcriptions ? (O/N): "
if /I "%CLEAN_CACHE%"=="O" (
    echo Nettoyage du cache...
    if exist "temp\*_transcript.json" del /Q "temp\*_transcript.json" 2>nul
    if exist "temp\*_audio.wav" del /Q "temp\*_audio.wav" 2>nul
    if exist "temp\concatenated_video.mp4" del /Q "temp\concatenated_video.mp4" 2>nul
    if exist "temp\concat_list.txt" del /Q "temp\concat_list.txt" 2>nul
    if exist "temp\project_autosave.json" del /Q "temp\project_autosave.json" 2>nul
    echo Cache nettoye!
    echo.
)

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

REM Verification que src\main.py existe
if not exist "src\main.py" (
    echo ERREUR: Le fichier src\main.py n'existe pas.
    echo Verifiez que vous etes dans le bon dossier.
    pause
    exit /b 1
)

REM Verification qu'Ollama est installe
where ollama >nul 2>nul
if errorlevel 1 (
    echo ERREUR: Ollama n'est pas installe ou n'est pas dans le PATH.
    echo Telechargez Ollama depuis: https://ollama.com/download
    echo.
    pause
    exit /b 1
)

REM Lancer Ollama en arriere-plan
echo Demarrage d'Ollama...
start /B ollama serve >nul 2>nul

REM Attendre qu'Ollama soit pret (max 10 secondes)
echo Attente du demarrage d'Ollama...
set OLLAMA_READY=0
for /L %%i in (1,1,10) do (
    curl -s http://127.0.0.1:11434/api/tags >nul 2>nul
    if not errorlevel 1 (
        set OLLAMA_READY=1
        goto :ollama_started
    )
    timeout /t 1 /nobreak >nul
)

:ollama_started
if %OLLAMA_READY%==1 (
    echo Ollama demarre avec succes!
) else (
    echo ATTENTION: Ollama ne repond pas encore, l'application utilisera le mode de secours.
)
echo.

REM Lancer l'application avec le Python de l'environnement virtuel
echo Lancement de l'application...
venv_312\Scripts\python.exe src\main.py

REM Si erreur, attendre avant de fermer
if errorlevel 1 (
    echo.
    echo Une erreur s'est produite.
    echo Consultez les logs dans le dossier logs/
    pause
)
