@echo off
echo ========================================
echo Mise a jour du Decoupeur Video Intelligent
echo ========================================
echo.

REM Verification de Git
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERREUR: Git n'est pas installe
    echo.
    echo Option 1: Installer Git depuis https://git-scm.com/download/win
    echo Option 2: Telecharger manuellement depuis GitHub:
    echo    https://github.com/King4Kats/OPCI-VIDEO-TEST-N2/archive/refs/heads/main.zip
    echo.
    pause
    exit /b 1
)

REM Sauvegarder les modifications locales si necessaire
echo [1/4] Verification des modifications locales...
git status --porcelain >nul 2>&1
if %errorLevel% neq 0 (
    echo Ce dossier n'est pas un repository Git valide.
    echo Telechargez la derniere version depuis:
    echo https://github.com/King4Kats/OPCI-VIDEO-TEST-N2/archive/refs/heads/main.zip
    pause
    exit /b 1
)

REM Recuperer les mises a jour
echo.
echo [2/4] Telechargement des mises a jour depuis GitHub...
git pull origin main

if %errorLevel% neq 0 (
    echo.
    echo ERREUR: Impossible de telecharger les mises a jour
    echo Verifiez votre connexion Internet ou essayez:
    echo   git fetch origin
    echo   git reset --hard origin/main
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
echo.
echo [3/4] Verification de l'environnement virtuel...
if not exist "venv_312\Scripts\activate.bat" (
    echo L'environnement virtuel n'existe pas.
    echo Lancez install.bat d'abord.
    pause
    exit /b 1
)

call venv_312\Scripts\activate.bat

REM Mettre a jour les dependances
echo.
echo [4/4] Mise a jour des dependances Python...
python -m pip install --upgrade pip
pip install -r requirements.txt --upgrade

if %errorLevel% neq 0 (
    echo.
    echo AVERTISSEMENT: Certaines dependances n'ont pas pu etre mises a jour
    echo L'application devrait quand meme fonctionner.
    pause
)

echo.
echo ========================================
echo Mise a jour terminee avec succes !
echo ========================================
echo.
echo Vous pouvez maintenant lancer l'application avec: launch.bat
echo.
pause
