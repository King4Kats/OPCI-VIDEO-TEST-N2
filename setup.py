# -*- coding: utf-8 -*-

"""
Script d'installation et de packaging pour le Découpeur Vidéo Intelligent
"""

import os
import sys
import shutil
import subprocess
import platform
import logging
from pathlib import Path

# Configuration
APP_NAME = "DecoupeurVideoIntelligent"
APP_VERSION = "1.0.0"
MAIN_SCRIPT = "src/main.py"
ICON_FILE = "assets/app_icon.ico" if platform.system() == "Windows" else "assets/app_icon.png"

# Chemins
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
INSTALLER_DIR = Path("installer")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AppBuilder:
    """Constructeur d'application pour créer l'exécutable et l'installeur"""

    def __init__(self):
        self.platform = platform.system()
        self.architecture = platform.machine()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        logger.info(f"Plateforme détectée: {self.platform} {self.architecture}")
        logger.info(f"Version Python: {self.python_version}")

    def check_dependencies(self):
        """Vérifie que toutes les dépendances sont installées"""
        logger.info("Vérification des dépendances...")

        required_packages = [
            'PyInstaller>=5.0',
            'PyQt5>=5.15',
            'ffmpeg-python',
            'openai-whisper',
            'ollama',
            'torch',
            'librosa'
        ]

        missing_packages = []

        for package in required_packages:
            try:
                if '>=') in package:
                    pkg_name = package.split('>=')[0]
                else:
                    pkg_name = package

                __import__(pkg_name.lower().replace('-', '_'))
                logger.info(f"✓ {pkg_name} installé")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"✗ {pkg_name} manquant")

        if missing_packages:
            logger.error("Dépendances manquantes:")
            for pkg in missing_packages:
                logger.error(f"  - {pkg}")
            logger.error("Installez avec: pip install " + " ".join(missing_packages))
            return False

        return True

    def check_external_tools(self):
        """Vérifie que les outils externes sont disponibles"""
        logger.info("Vérification des outils externes...")

        # Vérifier FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("✓ FFmpeg disponible")
            else:
                logger.warning("✗ FFmpeg non fonctionnel")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.error("✗ FFmpeg non trouvé")
            logger.error("Installez FFmpeg: https://ffmpeg.org/download.html")
            return False

        # Vérifier Ollama
        try:
            result = subprocess.run(['ollama', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("✓ Ollama disponible")
            else:
                logger.warning("✗ Ollama non fonctionnel")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("✗ Ollama non trouvé")
            logger.warning("Installez Ollama: https://ollama.ai/download")
            return False

        return True

    def clean_build_directories(self):
        """Nettoie les dossiers de build"""
        logger.info("Nettoyage des dossiers de build...")

        for directory in [BUILD_DIR, DIST_DIR]:
            if directory.exists():
                shutil.rmtree(directory)
                logger.info(f"Dossier {directory} supprimé")

    def create_spec_file(self):
        """Crée le fichier .spec pour PyInstaller"""
        logger.info("Création du fichier .spec...")

        # Modules cachés nécessaires
        hidden_imports = [
            'PyQt5.QtCore',
            'PyQt5.QtWidgets',
            'PyQt5.QtGui',
            'ffmpeg',
            'whisper',
            'torch',
            'librosa',
            'ollama',
            'numpy',
            'PIL',
            'pydub'
        ]

        # Données à inclure
        datas = [
            ('assets', 'assets'),
            ('README.md', '.'),
        ]

        # Binaires à inclure (FFmpeg si présent)
        binaries = []

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries={binaries},
    datas={datas},
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Application GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{ICON_FILE}' if Path(ICON_FILE).exists() else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{APP_NAME}'
)
'''

        spec_file = Path(f"{APP_NAME}.spec")
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)

        logger.info(f"Fichier {spec_file} créé")
        return spec_file

    def build_executable(self):
        """Construit l'exécutable avec PyInstaller"""
        logger.info("Construction de l'exécutable...")

        spec_file = self.create_spec_file()

        # Commande PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ]

        logger.info(f"Commande: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("✓ Exécutable créé avec succès")
            logger.info(f"Sortie: {result.stdout}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error("✗ Erreur lors de la création de l'exécutable")
            logger.error(f"Code de retour: {e.returncode}")
            logger.error(f"Sortie d'erreur: {e.stderr}")
            return False

    def create_installer_script(self):
        """Crée le script d'installation"""
        logger.info("Création du script d'installation...")

        INSTALLER_DIR.mkdir(exist_ok=True)

        if self.platform == "Windows":
            return self.create_windows_installer()
        else:
            return self.create_unix_installer()

    def create_windows_installer(self):
        """Crée l'installeur Windows avec NSIS ou un script batch"""
        installer_script = INSTALLER_DIR / "install.bat"

        script_content = f'''@echo off
echo ========================================
echo Installation du Decoupeur Video Intelligent
echo Version {APP_VERSION}
echo ========================================
echo.

REM Verification des droits administrateur
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERREUR: Ce script necessite les droits administrateur
    echo Faites un clic droit et selectionnez "Executer en tant qu'administrateur"
    pause
    exit /b 1
)

REM Creation du dossier d'installation
set INSTALL_DIR=%ProgramFiles%\\DecoupeurVideoIntelligent
echo Creation du dossier d'installation: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copie des fichiers
echo Copie des fichiers de l'application...
xcopy /E /I /Y "..\\dist\\{APP_NAME}" "%INSTALL_DIR%"

REM Creation du raccourci sur le bureau
echo Creation du raccourci sur le bureau...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PUBLIC%\\Desktop\\Decoupeur Video Intelligent.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{APP_NAME}.exe'; $Shortcut.Save()"

REM Creation du raccourci dans le menu Demarrer
echo Creation du raccourci dans le menu Demarrer...
if not exist "%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs\\DecoupeurVideoIntelligent" mkdir "%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs\\DecoupeurVideoIntelligent"
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs\\DecoupeurVideoIntelligent\\Decoupeur Video Intelligent.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{APP_NAME}.exe'; $Shortcut.Save()"

REM Installation des dependances systeme si necessaire
echo Verification des dependances systeme...

REM Verification de FFmpeg
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo AVERTISSEMENT: FFmpeg n'est pas installe ou non accessible
    echo Telechargez FFmpeg sur: https://ffmpeg.org/download.html
    echo Et ajoutez-le a votre PATH
)

REM Verification d'Ollama
ollama --version >nul 2>&1
if %errorLevel% neq 0 (
    echo AVERTISSEMENT: Ollama n'est pas installe
    echo Telechargez Ollama sur: https://ollama.ai/download
)

echo.
echo ========================================
echo Installation terminee !
echo ========================================
echo.
echo L'application a ete installee dans: %INSTALL_DIR%
echo Un raccourci a ete cree sur le bureau et dans le menu Demarrer
echo.
echo Pour une utilisation optimale, assurez-vous que:
echo - FFmpeg est installe et accessible
echo - Ollama est installe et configure
echo - Un modele Ollama est telecharge (ex: ollama pull mistral)
echo.
pause
'''

        with open(installer_script, 'w', encoding='utf-8') as f:
            f.write(script_content)

        logger.info(f"Script d'installation créé: {installer_script}")
        return installer_script

    def create_unix_installer(self):
        """Crée l'installeur Unix (Linux/macOS)"""
        installer_script = INSTALLER_DIR / "install.sh"

        script_content = f'''#!/bin/bash

echo "========================================"
echo "Installation du Découpeur Vidéo Intelligent"
echo "Version {APP_VERSION}"
echo "========================================"
echo

# Vérification des droits
if [ "$EUID" -ne 0 ]; then
    echo "ERREUR: Ce script nécessite les droits root"
    echo "Exécutez: sudo ./install.sh"
    exit 1
fi

# Dossier d'installation
INSTALL_DIR="/opt/DecoupeurVideoIntelligent"
echo "Création du dossier d'installation: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copie des fichiers
echo "Copie des fichiers de l'application..."
cp -r "../dist/{APP_NAME}"/* "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/{APP_NAME}"

# Création du script de lancement
echo "Création du script de lancement..."
cat > "/usr/local/bin/decoupeur-video" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
./{APP_NAME}
EOF
chmod +x "/usr/local/bin/decoupeur-video"

# Création du fichier .desktop
echo "Création du raccourci dans le menu..."
cat > "/usr/share/applications/decoupeur-video-intelligent.desktop" << EOF
[Desktop Entry]
Name=Découpeur Vidéo Intelligent
Comment=Découpage automatique de vidéos d'interviews
Exec=/usr/local/bin/decoupeur-video
Icon=$INSTALL_DIR/assets/app_icon.png
Terminal=false
Type=Application
Categories=AudioVideo;Video;
EOF

# Vérification des dépendances
echo "Vérification des dépendances système..."

# FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "AVERTISSEMENT: FFmpeg n'est pas installé"
    echo "Installez avec: sudo apt install ffmpeg (Ubuntu/Debian)"
    echo "ou: brew install ffmpeg (macOS)"
fi

# Ollama
if ! command -v ollama &> /dev/null; then
    echo "AVERTISSEMENT: Ollama n'est pas installé"
    echo "Téléchargez sur: https://ollama.ai/download"
fi

echo
echo "========================================"
echo "Installation terminée !"
echo "========================================"
echo
echo "L'application a été installée dans: $INSTALL_DIR"
echo "Vous pouvez la lancer avec: decoupeur-video"
echo "Ou via le menu des applications"
echo
echo "Pour une utilisation optimale, assurez-vous que:"
echo "- FFmpeg est installé"
echo "- Ollama est installé et configuré"
echo "- Un modèle Ollama est téléchargé (ex: ollama pull mistral)"
echo
'''

        with open(installer_script, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # Rendre le script exécutable
        os.chmod(installer_script, 0o755)

        logger.info(f"Script d'installation créé: {installer_script}")
        return installer_script

    def create_uninstaller(self):
        """Crée le script de désinstallation"""
        if self.platform == "Windows":
            uninstaller = INSTALLER_DIR / "uninstall.bat"
            script_content = f'''@echo off
echo Desinstallation du Decoupeur Video Intelligent...

set INSTALL_DIR=%ProgramFiles%\\DecoupeurVideoIntelligent

REM Suppression des fichiers
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo Dossier d'installation supprime
)

REM Suppression des raccourcis
del "%PUBLIC%\\Desktop\\Decoupeur Video Intelligent.lnk" 2>nul
rmdir /S /Q "%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs\\DecoupeurVideoIntelligent" 2>nul

echo Desinstallation terminee
pause
'''
        else:
            uninstaller = INSTALLER_DIR / "uninstall.sh"
            script_content = f'''#!/bin/bash

echo "Désinstallation du Découpeur Vidéo Intelligent..."

# Vérification des droits
if [ "$EUID" -ne 0 ]; then
    echo "ERREUR: Ce script nécessite les droits root"
    echo "Exécutez: sudo ./uninstall.sh"
    exit 1
fi

# Suppression des fichiers
INSTALL_DIR="/opt/DecoupeurVideoIntelligent"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "Dossier d'installation supprimé"
fi

# Suppression du script de lancement
rm -f "/usr/local/bin/decoupeur-video"

# Suppression du fichier .desktop
rm -f "/usr/share/applications/decoupeur-video-intelligent.desktop"

echo "Désinstallation terminée"
'''

        with open(uninstaller, 'w', encoding='utf-8') as f:
            f.write(script_content)

        if self.platform != "Windows":
            os.chmod(uninstaller, 0o755)

        logger.info(f"Script de désinstallation créé: {uninstaller}")

    def create_readme_installation(self):
        """Crée le README pour l'installation"""
        readme_path = INSTALLER_DIR / "README_INSTALLATION.md"

        readme_content = f'''# Installation du Découpeur Vidéo Intelligent

## Prérequis

### Obligatoires
- **FFmpeg**: Pour le traitement vidéo
  - Windows: Téléchargez sur https://ffmpeg.org/download.html et ajoutez au PATH
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`

- **Ollama**: Pour l'analyse IA locale
  - Téléchargez sur https://ollama.ai/download
  - Installez un modèle: `ollama pull mistral`

### Recommandés
- Au moins 8 GB de RAM
- Espace disque libre : 2 GB minimum
- GPU compatible (optionnel, pour accélérer Whisper)

## Installation

### Windows
1. Exécutez `install.bat` en tant qu'administrateur
2. Suivez les instructions à l'écran
3. L'application sera installée dans `C:\\Program Files\\DecoupeurVideoIntelligent`

### Linux/macOS
1. Exécutez `sudo ./install.sh`
2. Suivez les instructions à l'écran
3. L'application sera installée dans `/opt/DecoupeurVideoIntelligent`

## Utilisation

### Premier lancement
1. Démarrez l'application depuis le raccourci ou le menu
2. Vérifiez que FFmpeg et Ollama sont détectés
3. Sélectionnez vos fichiers vidéo (MTS, MP4, AVI)
4. Cliquez sur "Démarrer l'analyse"

### Formats supportés
- **Vidéo**: MTS, MP4, AVI, MOV, MKV
- **Sortie**: MP4 (H.264 + AAC)

## Dépannage

### Erreur FFmpeg
- Vérifiez que FFmpeg est installé : `ffmpeg -version`
- Ajoutez FFmpeg au PATH système

### Erreur Ollama
- Vérifiez qu'Ollama est installé : `ollama --version`
- Téléchargez un modèle : `ollama pull mistral`

### Performance lente
- Utilisez un GPU compatible
- Fermez les autres applications
- Vérifiez l'espace disque disponible

## Désinstallation

### Windows
Exécutez `uninstall.bat` en tant qu'administrateur

### Linux/macOS
Exécutez `sudo ./uninstall.sh`

## Support

- Logs : Consultez le dossier `logs/` dans l'installation
- GitHub : [Lien vers le repository]
- Documentation complète : Voir `docs/`

---

Version {APP_VERSION}
'''

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        logger.info(f"README d'installation créé: {readme_path}")

    def build_complete_package(self):
        """Construit le package complet avec installeur"""
        logger.info("Construction du package complet...")

        # 1. Vérifications
        if not self.check_dependencies():
            return False

        if not self.check_external_tools():
            logger.warning("Outils externes manquants - l'application pourrait ne pas fonctionner correctement")

        # 2. Nettoyage
        self.clean_build_directories()

        # 3. Construction de l'exécutable
        if not self.build_executable():
            return False

        # 4. Création des scripts d'installation
        self.create_installer_script()
        self.create_uninstaller()
        self.create_readme_installation()

        # 5. Récapitulatif
        logger.info("=" * 50)
        logger.info("CONSTRUCTION TERMINÉE")
        logger.info("=" * 50)
        logger.info(f"Exécutable: {DIST_DIR / APP_NAME}")
        logger.info(f"Installeur: {INSTALLER_DIR}")
        logger.info("=" * 50)

        return True


def main():
    """Point d'entrée principal"""
    print(f"""
╔══════════════════════════════════════════╗
║      Découpeur Vidéo Intelligent         ║
║              Builder v{APP_VERSION}              ║
╚══════════════════════════════════════════╝
""")

    builder = AppBuilder()

    try:
        success = builder.build_complete_package()

        if success:
            print("\n✓ Construction réussie !")
            print(f"\nFichiers générés:")
            print(f"- Exécutable: {DIST_DIR / APP_NAME}")
            print(f"- Installeur: {INSTALLER_DIR}")
            print(f"\nPour distribuer l'application:")
            print(f"1. Compressez le dossier {INSTALLER_DIR}")
            print(f"2. Incluez le dossier {DIST_DIR / APP_NAME}")
            print(f"3. Fournissez le README_INSTALLATION.md")

        else:
            print("\n✗ Construction échouée")
            return 1

    except KeyboardInterrupt:
        print("\n\nConstruction interrompue par l'utilisateur")
        return 1
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())