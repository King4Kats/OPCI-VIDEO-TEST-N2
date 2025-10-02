# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from config import Config

logger = logging.getLogger(__name__)


class ProjectState:
    """Gestionnaire de l'état du projet pour la sauvegarde/reprise"""

    def __init__(self):
        self.state_file = Config.TEMP_DIR / Config.AUTOSAVE_FILENAME
        self.current_state = {}

    def save_state(self, state_data: Dict[str, Any]) -> bool:
        """Sauvegarde l'état actuel du projet"""
        try:
            self.current_state.update(state_data)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_state, f, indent=2, ensure_ascii=False)
            logger.debug(f"État sauvegardé: {len(state_data)} éléments")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False

    def load_state(self) -> Optional[Dict[str, Any]]:
        """Charge l'état sauvegardé s'il existe"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.current_state = json.load(f)
                logger.info(f"État restauré: {len(self.current_state)} éléments")
                return self.current_state
            return None
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            return None

    def clear_state(self):
        """Supprime le fichier de sauvegarde"""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
            self.current_state = {}
            logger.debug("État nettoyé")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")

    def has_saved_state(self) -> bool:
        """Vérifie s'il existe un état sauvegardé"""
        return self.state_file.exists() and self.state_file.stat().st_size > 0


class FileValidator:
    """Validateur de fichiers vidéo"""

    @staticmethod
    def validate_video_file(file_path: str) -> tuple[bool, str]:
        """
        Valide un fichier vidéo
        Returns: (is_valid, error_message)
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return False, f"Le fichier n'existe pas: {file_path}"

            if not path.is_file():
                return False, f"Le chemin ne pointe pas vers un fichier: {file_path}"

            if path.suffix.lower() not in Config.SUPPORTED_VIDEO_FORMATS:
                return False, f"Format non supporté: {path.suffix}. Formats acceptés: {', '.join(Config.SUPPORTED_VIDEO_FORMATS)}"

            if path.stat().st_size == 0:
                return False, f"Le fichier est vide: {file_path}"

            if path.stat().st_size < 1024:  # Moins de 1KB
                return False, f"Le fichier semble trop petit pour être une vidéo valide: {file_path}"

            return True, ""

        except Exception as e:
            return False, f"Erreur lors de la validation: {str(e)}"

    @staticmethod
    def validate_video_files(file_paths: list) -> tuple[list, list]:
        """
        Valide une liste de fichiers vidéo
        Returns: (valid_files, errors)
        """
        valid_files = []
        errors = []

        for file_path in file_paths:
            is_valid, error = FileValidator.validate_video_file(file_path)
            if is_valid:
                valid_files.append(file_path)
            else:
                errors.append(error)

        return valid_files, errors


def ensure_directory_exists(path: str) -> bool:
    """S'assure qu'un dossier existe, le crée si nécessaire"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Impossible de créer le dossier {path}: {e}")
        return False


def clean_temp_files():
    """Nettoie les fichiers temporaires"""
    try:
        temp_dir = Config.TEMP_DIR
        if temp_dir.exists():
            for file_path in temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    logger.debug(f"Fichier temporaire supprimé: {file_path}")
        logger.info("Nettoyage des fichiers temporaires terminé")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")


def get_safe_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour le rendre sûr pour le système de fichiers"""
    # Caractères à remplacer
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    safe_filename = filename

    for char in invalid_chars:
        safe_filename = safe_filename.replace(char, '_')

    # Limiter la longueur
    if len(safe_filename) > 200:
        safe_filename = safe_filename[:200]

    return safe_filename.strip()