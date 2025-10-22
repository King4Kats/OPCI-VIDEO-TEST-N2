# -*- coding: utf-8 -*-

import os
from pathlib import Path

class Config:
    """Configuration globale de l'application"""

    # Chemins
    APP_DIR = Path(__file__).parent.parent
    SRC_DIR = APP_DIR / "src"
    ASSETS_DIR = APP_DIR / "assets"
    LOGS_DIR = APP_DIR / "logs"
    TEMP_DIR = APP_DIR / "temp"
    OUTPUT_DIR = APP_DIR / "output"

    # Transcription Whisper
    WHISPER_MODEL = "medium"  # small, base, medium, large
    WHISPER_LANGUAGE = "fr"
    SEGMENT_MAX_DURATION = 600  # 10 minutes maximum par segment

    # IA Analysis
    OLLAMA_MODEL = "qwen2.5:3b"  # Modèle léger optimisé pour l'analyse de texte (~2 GB RAM)
    MAX_TOKENS_PER_ANALYSIS = 4000

    # Vidéo
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mts', '.mov', '.mkv']
    OUTPUT_VIDEO_FORMAT = 'mp4'
    OUTPUT_VIDEO_CODEC = 'libx264'
    OUTPUT_AUDIO_CODEC = 'aac'
    VIDEO_QUALITY = 23  # CRF value (18-28 recommended)

    # Interface
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    PROGRESS_UPDATE_INTERVAL = 100  # ms

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5

    # Sauvegarde automatique
    AUTOSAVE_INTERVAL = 300  # 5 minutes
    AUTOSAVE_FILENAME = "project_autosave.json"

    @classmethod
    def create_directories(cls):
        """Crée les dossiers nécessaires s'ils n'existent pas"""
        for directory in [cls.LOGS_DIR, cls.TEMP_DIR, cls.OUTPUT_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_temp_audio_file(cls, video_filename):
        """Génère le nom de fichier audio temporaire"""
        return cls.TEMP_DIR / f"{Path(video_filename).stem}_audio.wav"

    @classmethod
    def get_temp_transcript_file(cls, video_filename):
        """Génère le nom de fichier de transcription temporaire"""
        return cls.TEMP_DIR / f"{Path(video_filename).stem}_transcript.json"