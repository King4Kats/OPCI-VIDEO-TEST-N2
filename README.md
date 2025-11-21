# Découpeur Vidéo Intelligent

**Version 2.0 - Production Ready**

Application Windows pour découper automatiquement des vidéos d'interviews en extraits thématiques.

---

## Installation Rapide

```cmd
git clone https://github.com/King4Kats/OPCI-VIDEO-TEST-N2.git
cd OPCI-VIDEO-TEST-N2
install.bat
```

 **[Guide détaillé →](QUICK_START.md)**

---

## Fonctionnalités

-  **Découpage automatique** par thèmes (pas par durée fixe)
-  **Transcription** haute qualité (OpenAI Whisper)
-  **Analyse IA** locale (Ollama)
-  **Support multi-formats**: MTS, MP4, AVI, MOV, MK
-  **100% local** (confidentialité garantie)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Interface Utilisateur (PyQt5)                │
│  Sélection │ Progression │ Édition │ Prévisualisation│
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│            Traitement Vidéo & Audio                  │
│    Concaténation │ Extraction │ Découpage            │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│              Services IA & Encodage                  │
│    FFmpeg │ Whisper │ Ollama                         │
└─────────────────────────────────────────────────────┘
```

### Workflow

```
Vidéo(s) → Extraction Audio → Transcription (Whisper)
    ↓
Analyse IA (Ollama) → Segments Thématiques
    ↓
Validation Utilisateur → Export MP4
```

---

## Prérequis

| Logiciel | Version | Installation |
|----------|---------|--------------|
| **Python** | 3.12+ | [python.org](https://www.python.org/downloads/) |
| **FFmpeg** | Latest | [Guide →](QUICK_START.md) |
| **Ollama** | Latest | [ollama.ai](https://ollama.ai/download) |

**Matériel recommandé:**
- RAM: 16 GB (minimum 8 GB)
- Disque: 20 GB libre
- OS: Windows 10/11 64-bit

---

## Utilisation

### 1. Lancer l'application

```cmd
launch.bat
```

### 2. Workflow Standard

1. **Importer** vidéo(s) → Sélectionner fichiers
2. **Analyser** → Clic "Démarrer l'analyse" (60-90 min pour 1h de vidéo)
3. **Valider** → Éditer les segments proposés
4. **Exporter** → Choisir dossier et exporter

### 3. Fichiers Générés

```
output/
├── transcriptions/
│   ├── [video]_transcription.txt
│   └── [video]_transcription.json
│
└── [dossier_choisi]/
    ├── 01_Theme1.mp4
    ├── 02_Theme2.mp4
    └── ...
```

---

## Configuration

Éditer `src/config.py`:

```python
# Modèles IA
WHISPER_MODEL = "medium"       # tiny, base, small, medium, large
OLLAMA_MODEL = "qwen2.5:3b"    # Modèle d'analyse

# Qualité vidéo
VIDEO_QUALITY = 23             # CRF: 18 (haute) - 28 (basse)
OUTPUT_AUDIO_BITRATE = '192k'  # 128k, 192k, 256k, 320k
```

**Pour machines puissantes (16+ GB):**
```python
WHISPER_MODEL = "large"
OLLAMA_MODEL = "qwen2.5:14b"
VIDEO_QUALITY = 18
```

**Pour machines modestes (8 GB):**
```python
WHISPER_MODEL = "small"
OLLAMA_MODEL = "qwen2.5:3b"
VIDEO_QUALITY = 28
```

---

## Performances

### Benchmarks (CPU moderne, 16 GB RAM)

Pour 1 heure de vidéo:

| Étape | Durée |
|-------|-------|
| Extraction audio | 10 sec |
| Transcription (medium) | 35-40 min |
| Analyse IA (qwen2.5:3b) | 8-12 min |
| Export (10 segments) | 10-15 min |
| **TOTAL** | **60-90 min** |

---

## Dépannage

###  FFmpeg non trouvé

```cmd
ffmpeg -version
# Si erreur, ajouter au PATH:
setx PATH "%PATH%;C:\ffmpeg\bin"
```

###  Ollama non disponible

```cmd
ollama list
ollama pull qwen2.5:3b
```

###  Erreur de mémoire

Éditer `src/config.py`:
```python
WHISPER_MODEL = "small"  # Au lieu de "medium"
```

###  L'application ne démarre pas

```cmd
# Voir les logs
notepad logs\video_cutter.log
```

---

## Structure du Projet

```
OPCI-VIDEO-TEST-N2/
├── src/                    # Code source
│   ├── main.py            # Point d'entrée
│   ├── config.py          # Configuration
│   ├── ui/                # Interface PyQt5
│   ├── video/             # Traitement vidéo
│   ├── transcription/     # Whisper
│   ├── ai_analysis/       # Ollama
│   ├── export/            # Export segments
│   └── utils/             # Utilitaires
│
├── assets/                 # Ressources
├── output/                 # Résultats
├── logs/                   # Logs
├── temp/                   # Temporaires
│
├── install.bat            # Installation
├── launch.bat             # Lancement
├── update.bat             # Mise à jour
│
├── README.md              # Ce fichier
├── QUICK_START.md         # Guide rapide
└── LICENSE                # Licence MIT
```

---

## Technologies

- **Interface**: PyQt5
- **Transcription**: OpenAI Whisper
- **IA**: Ollama (qwen2.5)
- **Vidéo**: FFmpeg
- **Audio**: Librosa, PyDub
- **Deep Learning**: PyTorch

---

## Licence

MIT License - Voir [LICENSE](LICENSE)

---

## Support

-  Documentation: [QUICK_START.md](QUICK_START.md)
-  Bug? Voir `logs/video_cutter.log`
-  Idées? Ouvrir une issue sur GitHub

---

**Version**: 2.0.0
**Dernière mise à jour**: Novembre 2025

