# -*- coding: utf-8 -*-

import logging
import logging.handlers
import sys
from pathlib import Path
from config import Config


def setup_logger():
    """Configure le système de logging de l'application"""

    # Créer le dossier de logs s'il n'existe pas
    Config.create_directories()

    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Supprimer les handlers existants
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Formatter commun
    formatter = logging.Formatter(Config.LOG_FORMAT)

    # Handler pour les fichiers (avec rotation)
    log_file = Config.LOGS_DIR / "video_cutter.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=Config.LOG_MAX_SIZE,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Handler pour la console (seulement INFO et plus)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Logger spécifique pour les erreurs utilisateur
    user_logger = logging.getLogger('user_errors')
    error_file = Config.LOGS_DIR / "user_errors.log"
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    user_logger.addHandler(error_handler)

    return root_logger


def log_user_error(message, exception=None):
    """Log spécifique pour les erreurs utilisateur avec message en français"""
    user_logger = logging.getLogger('user_errors')
    if exception:
        user_logger.error(f"{message} - Détails: {str(exception)}")
    else:
        user_logger.error(message)