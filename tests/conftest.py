# -*- coding: utf-8 -*-

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def temp_dir():
    """Crée un dossier temporaire pour les tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_video_path(temp_dir):
    """Crée un fichier vidéo factice pour les tests"""
    video_path = temp_dir / "sample_video.mp4"
    video_path.write_bytes(b"fake video content")
    return str(video_path)


@pytest.fixture
def sample_transcript():
    """Transcription d'exemple pour les tests"""
    return {
        "text": "Bonjour, je m'appelle Jean et je suis artisan boulanger depuis 30 ans. J'ai appris le métier avec mon père dans notre village de Provence. Aujourd'hui, les techniques ont évolué mais l'essentiel reste le même.",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 15.5,
                "text": "Bonjour, je m'appelle Jean et je suis artisan boulanger depuis 30 ans.",
                "confidence": 0.95,
                "words_count": 12
            },
            {
                "id": 1,
                "start": 16.0,
                "end": 35.2,
                "text": "J'ai appris le métier avec mon père dans notre village de Provence.",
                "confidence": 0.92,
                "words_count": 12
            },
            {
                "id": 2,
                "start": 36.0,
                "end": 50.8,
                "text": "Aujourd'hui, les techniques ont évolué mais l'essentiel reste le même.",
                "confidence": 0.88,
                "words_count": 11
            }
        ],
        "metadata": {
            "total_duration": 50.8,
            "total_words": 35,
            "words_per_minute": 41.3,
            "average_confidence": 0.92,
            "segments_count": 3,
            "transcription_model": "medium"
        }
    }


@pytest.fixture
def sample_segments():
    """Segments d'exemple pour les tests"""
    return [
        {
            "title": "Présentation de l'artisan",
            "start_time": 0.0,
            "end_time": 15.5,
            "start_seconds": 0.0,
            "end_seconds": 15.5,
            "duration": "15s",
            "summary": "Jean se présente comme boulanger depuis 30 ans",
            "keywords": ["Jean", "artisan", "boulanger", "30 ans"],
            "importance": 4,
            "theme_based": True
        },
        {
            "title": "Apprentissage du métier",
            "start_time": 16.0,
            "end_time": 35.2,
            "start_seconds": 16.0,
            "end_seconds": 35.2,
            "duration": "19s",
            "summary": "Apprentissage avec son père en Provence",
            "keywords": ["apprentissage", "père", "village", "Provence"],
            "importance": 5,
            "theme_based": True
        },
        {
            "title": "Évolution des techniques",
            "start_time": 36.0,
            "end_time": 50.8,
            "start_seconds": 36.0,
            "end_seconds": 50.8,
            "duration": "14s",
            "summary": "Les techniques ont évolué mais l'essentiel reste",
            "keywords": ["techniques", "évolué", "essentiel"],
            "importance": 3,
            "theme_based": True
        }
    ]


@pytest.fixture
def mock_ffmpeg():
    """Mock pour FFmpeg"""
    with patch('subprocess.run') as mock_run:
        # Simuler ffmpeg -version
        mock_run.return_value = Mock(
            returncode=0,
            stdout="ffmpeg version 4.4.0",
            stderr=""
        )
        yield mock_run


@pytest.fixture
def mock_whisper():
    """Mock pour Whisper"""
    with patch('whisper.load_model') as mock_load:
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "Sample transcription",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 10.0,
                    "text": "Sample transcription"
                }
            ]
        }
        mock_load.return_value = mock_model
        yield mock_model


@pytest.fixture
def mock_ollama():
    """Mock pour Ollama"""
    with patch('ollama.Client') as mock_client:
        mock_instance = Mock()
        mock_instance.list.return_value = {
            "models": [{"name": "qwen2.5:3b"}]
        }
        mock_instance.chat.return_value = {
            "message": {
                "content": """{
                    "themes": [
                        {
                            "title": "Test Theme",
                            "description": "Test description",
                            "start_approximate": 0.0,
                            "end_approximate": 10.0,
                            "keywords": ["test"],
                            "importance": 3
                        }
                    ],
                    "cut_points": [],
                    "locations": [],
                    "global_keywords": ["test"]
                }"""
            }
        }
        mock_client.return_value = mock_instance
        yield mock_instance