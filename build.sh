#!/bin/bash

echo "========================================"
echo "Construction du Découpeur Vidéo Intelligent"
echo "========================================"
echo

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "ERREUR: Python 3 n'est pas installé"
    echo "Installez Python 3.8 ou plus récent"
    exit 1
fi

# Installation des dépendances de build
echo "Installation des dépendances de build..."
pip3 install pyinstaller>=5.0

# Lancement du build
echo "Lancement de la construction..."
python3 setup.py

echo
echo "Construction terminée !"