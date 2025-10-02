#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator, QLocale

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from ui.main_window import MainWindow
from utils.logger import setup_logger


def main():
    """Point d'entrée principal de l'application"""

    # Configuration des logs
    setup_logger()
    logger = logging.getLogger(__name__)

    try:
        # Création de l'application Qt
        app = QApplication(sys.argv)
        app.setApplicationName("Découpeur Vidéo Intelligent")
        app.setApplicationVersion("1.0.0")

        # Configuration de la langue (français)
        locale = QLocale(QLocale.French, QLocale.France)
        QLocale.setDefault(locale)

        # Création et affichage de la fenêtre principale
        window = MainWindow()
        window.show()

        logger.info("Application démarrée avec succès")

        # Lancement de la boucle d'événements
        sys.exit(app.exec_())

    except Exception as e:
        logger.critical(f"Erreur critique lors du démarrage : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()