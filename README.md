# Decoupeur Video Intelligent

**Version 1.0**

Logiciel Windows pour decouper automatiquement des videos d'interviews en extraits thematiques grace a l'intelligence artificielle.

---

## Fonctionnalites

- **Concatenation automatique** des fichiers MTS multiples
- **Transcription audio** avec Whisper (OpenAI)
- **Analyse thematique IA** avec Ollama pour identifier les sujets
- **Decoupage intelligent** par theme (pas par duree fixe)
- **Export de la transcription** en texte et JSON
- **Previsualisation** des segments
- **Interface graphique** simple et intuitive

---

## Installation sur un nouveau PC Windows

### Prerequis

1. **Windows 10/11** (64 bits)
2. **Python 3.12** - [Telecharger ici](https://www.python.org/downloads/)
   - Lors de l'installation, cocher **"Add Python to PATH"**
3. **FFmpeg** - [Guide d'installation](#installation-ffmpeg)
4. **Ollama** - [Guide d'installation](#installation-ollama)

### Installation FFmpeg

1. Telecharger FFmpeg: https://www.gyan.dev/ffmpeg/builds/
   - Choisir **ffmpeg-release-essentials.zip**
2. Extraire le ZIP dans `C:\ffmpeg`
3. Ajouter au PATH Windows:
   - Panneau de configuration > Systeme > Parametres systeme avances
   - Variables d'environnement
   - Dans "Variables systeme", modifier `Path`
   - Ajouter: `C:\ffmpeg\bin`
4. Verifier l'installation:
   ```cmd
   ffmpeg -version
   ```

### Installation Ollama

1. Telecharger Ollama: https://ollama.ai/download
2. Installer l'application
3. Ouvrir un terminal et telecharger un modele:
   ```cmd
   ollama pull mistral
   ```
   OU pour de meilleurs resultats (plus lourd):
   ```cmd
   ollama pull qwen3-coder:30b
   ```

### Installation de l'application

1. **Telecharger** le dossier complet du projet
2. **Ouvrir un terminal** dans le dossier du projet
3. **Creer l'environnement virtuel**:
   ```cmd
   python -m venv venv_312
   ```
4. **Activer l'environnement**:
   ```cmd
   venv_312\Scripts\activate
   ```
5. **Installer les dependances**:
   ```cmd
   pip install -r requirements.txt
   ```

### Premier lancement

Double-cliquer sur `launch.bat` OU executer:
```cmd
venv_312\Scripts\python src\main.py
```

---

## Guide d'utilisation

### 1. Demarrage
- Lancer l'application via `launch.bat`
- Verifier que FFmpeg et Ollama sont detectes

### 2. Selection des fichiers
- Cliquer sur "Selectionner les fichiers video"
- Choisir un ou plusieurs fichiers (MTS, MP4, AVI, MOV, MKV)
- Les fichiers MTS multiples seront automatiquement concatenes

### 3. Traitement
- Cliquer sur "Demarrer l'analyse"
- Attendre la fin du traitement (10-60 min selon la duree)
- Suivre la progression dans l'interface

**Etapes du traitement:**
1. Concatenation des fichiers (si plusieurs)
2. Extraction de l'audio
3. Transcription Whisper
4. Export de la transcription (TXT + JSON)
5. Analyse IA des themes
6. Creation des segments

### 4. Validation des segments
- Consulter la liste des segments proposes
- Double-cliquer sur un segment pour l'editer
- Modifier les titres, ajuster les timestamps
- Previsualiser un segment (bouton "Previsualiser")

### 5. Export final
- Cliquer sur "Choisir le dossier de sortie"
- Selectionner le dossier de destination
- Cliquer sur "Exporter tous les segments"
- Attendre la fin de l'export

---

## Structure des fichiers generes

```
output/
├── transcriptions/
│   ├── [nom_video]_transcription.txt    # Transcription complete avec timestamps
│   └── [nom_video]_transcription.json   # Donnees structurees
│
└── [dossier_choisi]/
    ├── 01_Titre_du_theme.mp4
    ├── 02_Autre_theme.mp4
    └── ...
```

---

## Configuration

### Modeles IA

Par defaut, l'application utilise:
- **Whisper**: `medium` (bon compromis qualite/vitesse)
- **Ollama**: `qwen3-coder:30b` (ou `mistral` si installe)

Pour changer les modeles, editer `src/config.py`:
```python
WHISPER_MODEL = 'small'  # Options: tiny, base, small, medium, large
OLLAMA_MODEL = 'mistral'  # Ou tout autre modele Ollama
```

### Qualite video

Dans `src/config.py`:
```python
VIDEO_QUALITY = 23  # 0 (meilleure) a 51 (pire), defaut: 23
OUTPUT_VIDEO_CODEC = 'libx264'  # Codec video
OUTPUT_AUDIO_CODEC = 'aac'  # Codec audio
```

---

## Performances attendues

Sur un PC moderne (CPU uniquement):
- **Concatenation**: 1-2 min pour 8 fichiers MTS
- **Extraction audio**: 5-10 secondes
- **Transcription Whisper**: ~6-7 min par 10 min de video
- **Analyse IA**: ~2-3 min par chunk (4 chunks pour 1h de video)
- **Export video**: ~1 min par segment

**Total pour 1h de video**: ~60-90 minutes

---

## Depannage

### "FFmpeg non trouve"
```cmd
# Verifier l'installation
ffmpeg -version

# Ajouter au PATH si necessaire
setx PATH "%PATH%;C:\ffmpeg\bin"
```

### "Modele Ollama non disponible"
```cmd
# Verifier Ollama
ollama list

# Telecharger un modele
ollama pull mistral
```

### "Erreur de memoire"
- Fermer les autres applications
- Utiliser un modele Whisper plus petit (`small` au lieu de `medium`)
- Verifier l'espace disque disponible (min 5 GB)

### L'analyse IA ne fonctionne pas
- Verifier qu'Ollama est lance (icone dans la barre des taches)
- Relancer Ollama si necessaire
- Verifier qu'un modele est installe: `ollama list`

### Logs de diagnostic
Les logs sont disponibles dans: `logs/video_cutter.log`

---

## Limitations connues

- **GPU**: Supporte uniquement CPU pour Whisper (support GPU a venir)
- **Formats video**: Optimise pour MTS, MP4, AVI, MOV, MKV
- **Langues**: Optimise pour le francais (configurable)
- **Duree max**: Pas de limite theorique, mais >2h peut etre long

---

## Support et contact

Pour signaler un bug ou demander une fonctionnalite:
- Consulter les logs dans `logs/`
- Noter la version de l'application et de l'OS
- Decrire les etapes pour reproduire le probleme

---

## Licence

MIT License - Voir le fichier [LICENSE](LICENSE) pour plus de details

---

## Credits

- [OpenAI Whisper](https://github.com/openai/whisper) - Transcription audio
- [Ollama](https://ollama.ai/) - Modeles IA locaux
- [FFmpeg](https://ffmpeg.org/) - Traitement video
- PyQt5, PyTorch, Librosa - Frameworks Python

---

**Version**: 1.0
**Derniere mise a jour**: Octobre 2025
