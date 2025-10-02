# Assets - Découpeur Vidéo Intelligent

Ce dossier contient les ressources statiques de l'application.

## Icônes et images

### Icons requis
- `app_icon.ico` (Windows, 32x32, 48x48, 256x256)
- `app_icon.png` (Linux/macOS, 512x512)
- `app_icon.icns` (macOS, optionnel)

### Suggestion pour créer les icônes
Vous pouvez utiliser un service en ligne comme :
- https://convertio.co/png-ico/
- https://www.icoconverter.com/

Ou utiliser ImageMagick :
```bash
# Créer un ICO multi-tailles depuis un PNG
convert icon.png -resize 256x256 -define icon:auto-resize=256,128,96,64,48,32,16 app_icon.ico

# Créer un ICNS pour macOS
png2icns app_icon.icns icon_512.png icon_256.png icon_128.png icon_64.png icon_32.png icon_16.png
```

## Structure recommandée
```
assets/
├── icons/
│   ├── app_icon.ico      # Icône Windows
│   ├── app_icon.png      # Icône Linux/général
│   └── app_icon.icns     # Icône macOS (optionnel)
├── images/
│   ├── splash_screen.png # Écran de démarrage (optionnel)
│   └── logo.png          # Logo de l'application
└── docs/
    └── screenshots/      # Captures d'écran pour documentation
```

## Note importante
Les fichiers d'icônes ne sont pas inclus dans ce repository pour des raisons de taille.

Pour générer un package complet, ajoutez vos propres icônes ou utilisez les icônes par défaut du système.