@echo off
echo ========================================
echo Construction du Decoupeur Video Intelligent
echo ========================================
echo.

REM Verification de Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERREUR: Python n'est pas installe ou non accessible
    echo Telechargez Python sur: https://python.org
    pause
    exit /b 1
)

REM Installation des dependances de build
echo Installation des dependances de build...
pip install pyinstaller>=5.0

REM Lancement du build
echo Lancement de la construction...
python setup.py

echo.
echo Construction terminee !
pause