# Guide d'Installation - Decoupeur Video Intelligent

## Installation Complete sur Nouveau PC Windows

### Etape 1: Installer Python 3.12

1. Telecharger Python 3.12: https://www.python.org/downloads/
2. Lancer l'installeur
3. **IMPORTANT**: Cocher "Add Python to PATH"
4. Cliquer sur "Install Now"
5. Verifier l'installation:
   ```cmd
   python --version
   ```
   Doit afficher: `Python 3.12.x`

### Etape 2: Installer FFmpeg

1. Telecharger FFmpeg: https://www.gyan.dev/ffmpeg/builds/
   - Choisir **ffmpeg-release-essentials.zip**
2. Extraire le ZIP dans `C:\ffmpeg`
3. Ajouter au PATH Windows:
   - Touche Windows > Taper "variables d'environnement"
   - Cliquer sur "Modifier les variables d'environnement systeme"
   - Bouton "Variables d'environnement"
   - Dans "Variables systeme", selectionner `Path` et cliquer "Modifier"
   - Cliquer "Nouveau"
   - Ajouter: `C:\ffmpeg\bin`
   - Cliquer OK sur toutes les fenetres
4. **IMPORTANT**: Fermer et rouvrir le terminal
5. Verifier l'installation:
   ```cmd
   ffmpeg -version
   ```

### Etape 3: Installer Ollama

1. Telecharger Ollama: https://ollama.ai/download
2. Lancer l'installeur et suivre les instructions
3. Ouvrir un terminal (cmd)
4. Telecharger le modele IA (recommande):
   ```cmd
   ollama pull qwen2.5:3b
   ```

   Le telechargement est d'environ 2 GB et peut prendre 5-15 minutes.

   **Alternatives** (si vous avez plus de RAM disponible):
   - `ollama pull mistral:7b` (~4-5 GB RAM)
   - `ollama pull gemma2:9b` (~6 GB RAM)

5. Verifier l'installation:
   ```cmd
   ollama list
   ```

### Etape 4: Installer l'Application

1. Copier le dossier complet du projet sur votre PC
2. Ouvrir un terminal dans le dossier du projet:
   - Shift + Clic droit dans le dossier
   - "Ouvrir une fenetre PowerShell ici" ou "Ouvrir dans Terminal"

3. Creer l'environnement virtuel Python:
   ```cmd
   python -m venv venv_312
   ```

4. Activer l'environnement virtuel:
   ```cmd
   venv_312\Scripts\activate
   ```
   Le terminal doit maintenant afficher `(venv_312)` au debut de la ligne.

5. Installer les dependances Python:
   ```cmd
   pip install -r requirements.txt
   ```

   Cette etape peut prendre 10-30 minutes (telechargement de ~2-3 GB).

### Etape 5: Premier Lancement

Double-cliquer sur `launch.bat`

OU dans le terminal:
```cmd
venv_312\Scripts\python src\main.py
```

L'application devrait s'ouvrir.

---

## Verification de l'Installation

Pour verifier que tout est installe correctement:

1. Python:
   ```cmd
   python --version
   ```
   Doit afficher: `Python 3.12.x`

2. FFmpeg:
   ```cmd
   ffmpeg -version
   ```
   Doit afficher la version de FFmpeg

3. Ollama:
   ```cmd
   ollama list
   ```
   Doit afficher au moins un modele (qwen2.5:3b recommande)

4. Dependances Python:
   ```cmd
   venv_312\Scripts\activate
   pip list
   ```
   Doit afficher une longue liste incluant PyQt5, torch, whisper, ollama, etc.

---

## Problemes Courants

### "python n'est pas reconnu"
- Reinstaller Python et cocher "Add Python to PATH"
- OU ajouter manuellement Python au PATH:
  - Ajouter: `C:\Users\[VotreNom]\AppData\Local\Programs\Python\Python312`
  - Ajouter: `C:\Users\[VotreNom]\AppData\Local\Programs\Python\Python312\Scripts`

### "ffmpeg n'est pas reconnu"
- Verifier que `C:\ffmpeg\bin` existe
- Verifier que le PATH contient `C:\ffmpeg\bin`
- Fermer et rouvrir le terminal apres modification du PATH

### "ollama n'est pas reconnu"
- Relancer Ollama depuis le menu Demarrer
- Verifier qu'Ollama est lance (icone dans la barre des taches)

### L'installation de pip prend trop de temps
- Verifier la connexion Internet
- Certains packages (torch, librosa) sont volumineux (plusieurs GB)
- Laisser l'installation se terminer, ca peut prendre 30 minutes

### Erreur lors de l'installation de pip
- Mettre a jour pip:
  ```cmd
  python -m pip install --upgrade pip
  ```
- Reessayer l'installation:
  ```cmd
  pip install -r requirements.txt
  ```

---

## Espace Disque Requis

- Python 3.12: ~100 MB
- FFmpeg: ~100 MB
- Ollama + Modele qwen2.5:3b: ~2 GB
- Dependances Python (venv): ~3-4 GB
- Espace de travail (temp): 5-10 GB minimum

**Total minimum**: ~10-12 GB

---

## Prochaines Etapes

Une fois l'installation terminee, consulter le [README.md](README.md) pour:
- Guide d'utilisation
- Configuration des modeles
- Optimisation des performances
- Depannage avance

---

**Version**: 1.0
**Derniere mise a jour**: Octobre 2025
