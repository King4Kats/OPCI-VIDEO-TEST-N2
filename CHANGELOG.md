# Changelog - Decoupeur Video Intelligent

Toutes les modifications notables de ce projet seront documentees dans ce fichier.

---

## [1.0.1] - 2025-10-31

### Ajoute
- Script `install.bat` pour installation automatique
- Script `update.bat` pour mise a jour automatique depuis GitHub
- Verification des prerequis dans `launch.bat`
- Documentation de mise a jour dans README.md
- Ce fichier CHANGELOG.md

### Corrige
- Erreur de syntaxe dans `setup.py` ligne 59 (`'>=')` → `'>='`)
- `launch.bat` plante si `venv_312` n'existe pas
- Messages d'erreur plus clairs pour les problemes de chemin

### Ameliore
- `launch.bat` verifie maintenant l'existence de l'environnement virtuel
- Messages d'erreur plus explicites avec instructions de resolution
- Documentation README avec 3 methodes de mise a jour

---

## [1.0.0] - 2025-10-30

### Premiere version
- Concatenation automatique des fichiers MTS
- Transcription audio avec Whisper (OpenAI)
- Analyse thematique IA avec Ollama
- Decoupage intelligent par theme
- Export de la transcription en TXT et JSON
- Previsualisation des segments
- Interface graphique PyQt5
- Support formats: MTS, MP4, AVI, MOV, MKV
- Optimisation pour modele Qwen2.5:3b (leger, ~2GB RAM)

---

## Format

Le format est base sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet respecte [Semantic Versioning](https://semver.org/lang/fr/).

### Types de changements
- **Ajoute** : nouvelles fonctionnalites
- **Modifie** : changements aux fonctionnalites existantes
- **Deprecie** : fonctionnalites bientot supprimees
- **Supprime** : fonctionnalites supprimees
- **Corrige** : corrections de bugs
- **Securite** : correctifs de vulnerabilites
