# Guide de Démarrage Rapide

**Découpeur Vidéo Intelligent - Version 2.0**

---

## Installation (10 minutes)

### 1. Installer les Prérequis

**Python 3.12+**
1. Télécharger: https://www.python.org/downloads/
2. ⚠️ Cocher "Add Python to PATH" lors de l'installation

**FFmpeg**
1. Télécharger: https://www.gyan.dev/ffmpeg/builds/ (ffmpeg-release-essentials.zip)
2. Extraire dans `C:\ffmpeg`
3. Ajouter au PATH: `C:\ffmpeg\bin`
4. Vérifier: `ffmpeg -version`

**Ollama**
1. Télécharger: https://ollama.ai/download
2. Installer et lancer
3. Télécharger le modèle:
   ```cmd
   ollama pull qwen2.5:3b
   ```

### 2. Installer l'Application

```cmd
git clone https://github.com/King4Kats/OPCI-VIDEO-TEST-N2.git
cd OPCI-VIDEO-TEST-N2
install.bat
```

### 3. Lancer

```cmd
launch.bat
```

---

## Utilisation

### Workflow en 4 Étapes

**1️⃣ Importer une vidéo**
- Cliquer sur "Sélectionner les fichiers vidéo"
- Choisir votre/vos fichier(s) (MTS, MP4, AVI, MOV, MKV)

**2️⃣ Lancer l'analyse**
- Cliquer sur "Démarrer l'analyse"
- ⏱️ Attendre 60-90 min (pour 1h de vidéo)

**3️⃣ Valider les segments**
- Consulter la liste des segments générés
- Double-cliquer pour éditer les titres
- Prévisualiser pour vérifier

**4️⃣ Exporter**
- Cliquer sur "Choisir le dossier de sortie"
- Cliquer sur "Exporter tous les segments"

### Fichiers Générés

```
output/
├── transcriptions/
│   └── [video]_transcription.txt
└── [dossier_choisi]/
    ├── 01_Theme1.mp4
    ├── 02_Theme2.mp4
    └── ...
```

---

## Résolution de Problèmes

### ❌ FFmpeg non trouvé
```cmd
ffmpeg -version
# Si erreur, ajouter au PATH:
setx PATH "%PATH%;C:\ffmpeg\bin"
```

### ❌ Ollama non disponible
```cmd
ollama list
ollama pull qwen2.5:3b
```

### ❌ Erreur de mémoire
Éditer `src/config.py`:
```python
WHISPER_MODEL = "small"  # Au lieu de "medium"
```

### ❌ Application ne se lance pas
```cmd
notepad logs\video_cutter.log
```

---

## Configuration

### Pour Machines Puissantes (16+ GB)
```python
# Dans src/config.py
WHISPER_MODEL = "large"
OLLAMA_MODEL = "qwen2.5:14b"
VIDEO_QUALITY = 18
```

### Pour Machines Modestes (8 GB)
```python
# Dans src/config.py
WHISPER_MODEL = "small"
OLLAMA_MODEL = "qwen2.5:3b"
VIDEO_QUALITY = 28
```

---

## Ressources

- **Documentation complète**: [README.md](README.md)
- **Logs**: `logs/video_cutter.log`
- **Support**: Ouvrir une issue sur GitHub

---

**Bon découpage! 🎬✂️**
