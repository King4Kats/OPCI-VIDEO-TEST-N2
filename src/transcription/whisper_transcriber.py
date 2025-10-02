# -*- coding: utf-8 -*-

import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import whisper
import torch

from config import Config
from utils.file_manager import ensure_directory_exists

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Transcripteur utilisant OpenAI Whisper avec gestion des segments longs"""

    def __init__(self):
        self.model = None
        self.model_name = Config.WHISPER_MODEL
        self.language = Config.WHISPER_LANGUAGE
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Whisper configuré: modèle={self.model_name}, device={self.device}")

    def load_model(self) -> bool:
        """Charge le modèle Whisper en mémoire"""
        try:
            logger.info(f"Chargement du modèle Whisper: {self.model_name}")
            start_time = time.time()

            self.model = whisper.load_model(
                self.model_name,
                device=self.device,
                download_root=str(Config.TEMP_DIR)
            )

            load_time = time.time() - start_time
            logger.info(f"Modèle chargé en {load_time:.2f} secondes")
            return True

        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle Whisper: {e}")
            return False

    def get_audio_duration(self, audio_path: str) -> float:
        """Récupère la durée d'un fichier audio"""
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            logger.debug(f"Durée audio: {duration:.2f}s")
            return duration
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la durée: {e}")
            return 0.0

    def split_audio_into_segments(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Divise un long fichier audio en segments pour Whisper
        Returns: Liste de segments avec start_time, end_time, segment_path
        """
        duration = self.get_audio_duration(audio_path)
        max_duration = Config.SEGMENT_MAX_DURATION

        if duration <= max_duration:
            # Fichier assez court, pas besoin de diviser
            return [{
                'start_time': 0.0,
                'end_time': duration,
                'segment_path': audio_path,
                'segment_index': 0
            }]

        logger.info(f"Division du fichier audio en segments de {max_duration}s max")

        segments = []
        current_time = 0.0
        segment_index = 0

        while current_time < duration:
            end_time = min(current_time + max_duration, duration)

            segment_info = {
                'start_time': current_time,
                'end_time': end_time,
                'segment_path': audio_path,  # On utilisera le timestamp lors de la transcription
                'segment_index': segment_index
            }

            segments.append(segment_info)
            logger.debug(f"Segment {segment_index}: {current_time:.2f}s -> {end_time:.2f}s")

            current_time = end_time
            segment_index += 1

        logger.info(f"Audio divisé en {len(segments)} segments")
        return segments

    def extract_audio_segment(self, audio_path: str, start_time: float, end_time: float, output_path: str) -> str:
        """Extrait un segment d'un fichier audio"""
        try:
            import soundfile as sf
            import librosa

            # Charger l'audio
            y, sr = librosa.load(audio_path, sr=None)

            # Calculer les indices de début et fin
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)

            # Extraire le segment
            segment = y[start_sample:end_sample]

            # Sauvegarder
            sf.write(output_path, segment, sr)
            logger.debug(f"Segment audio extrait: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du segment audio: {e}")
            raise

    def transcribe_segment(self, audio_path: str, start_time: float = 0.0, end_time: float = None) -> Dict[str, Any]:
        """Transcrit un segment audio spécifique"""
        try:
            # Options de transcription
            options = {
                'language': self.language,
                'task': 'transcribe',
                'fp16': torch.cuda.is_available(),  # Optimisation GPU si disponible
                'verbose': False
            }

            logger.debug(f"Transcription segment: {start_time:.2f}s -> {end_time or 'fin'}s")

            # Si on doit transcrire un segment spécifique, extraire ce segment d'abord
            if start_time > 0 or end_time is not None:
                from pathlib import Path
                segment_path = Config.TEMP_DIR / f"audio_segment_{start_time:.0f}_{end_time:.0f}.wav"

                try:
                    self.extract_audio_segment(audio_path, start_time, end_time or start_time + 600, str(segment_path))

                    # Transcrire le segment extrait
                    result = self.model.transcribe(str(segment_path), **options)

                    # Ajuster les timestamps pour correspondre au fichier original
                    for segment in result['segments']:
                        segment['start'] += start_time
                        segment['end'] += start_time

                    # Nettoyer le fichier temporaire
                    if segment_path.exists():
                        segment_path.unlink()

                except Exception as e:
                    logger.warning(f"Erreur extraction segment, transcription complète: {e}")
                    # Fallback: transcrire tout le fichier
                    result = self.model.transcribe(audio_path, **options)
            else:
                # Transcrire tout le fichier
                result = self.model.transcribe(audio_path, **options)

            return result

        except Exception as e:
            logger.error(f"Erreur lors de la transcription du segment: {e}")
            raise

    def merge_transcription_results(self, segment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fusionne les résultats de transcription de plusieurs segments
        en une transcription cohérente avec timestamps corrects
        """
        logger.info(f"Fusion de {len(segment_results)} résultats de transcription")

        merged_text = []
        merged_segments = []

        for result in segment_results:
            merged_text.append(result['text'].strip())
            merged_segments.extend(result['segments'])

        # Résultat fusionné
        merged_result = {
            'text': ' '.join(merged_text),
            'segments': merged_segments,
            'language': segment_results[0].get('language', self.language) if segment_results else self.language
        }

        logger.info(f"Transcription fusionnée: {len(merged_result['segments'])} segments, {len(merged_result['text'])} caractères")
        return merged_result

    def enhance_transcript_with_metadata(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit la transcription avec des métadonnées utiles"""

        enhanced_segments = []

        for segment in transcript['segments']:
            enhanced_segment = {
                'id': segment['id'],
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'words_count': len(segment['text'].split()),
                'duration': segment['end'] - segment['start'],
                'confidence': segment.get('avg_logprob', 0.0),  # Score de confiance Whisper
                'no_speech_prob': segment.get('no_speech_prob', 0.0)
            }

            # Détection des pauses longues (potentiels points de coupe)
            if enhanced_segment['duration'] > 5.0:  # Plus de 5 secondes
                enhanced_segment['potential_cut_point'] = True

            enhanced_segments.append(enhanced_segment)

        # Calcul de statistiques globales
        total_duration = max([s['end'] for s in enhanced_segments]) if enhanced_segments else 0
        total_words = sum([s['words_count'] for s in enhanced_segments])
        avg_confidence = sum([s['confidence'] for s in enhanced_segments]) / len(enhanced_segments) if enhanced_segments else 0

        enhanced_transcript = {
            'text': transcript['text'],
            'segments': enhanced_segments,
            'language': transcript.get('language', self.language),
            'metadata': {
                'total_duration': total_duration,
                'total_words': total_words,
                'words_per_minute': (total_words / total_duration * 60) if total_duration > 0 else 0,
                'average_confidence': avg_confidence,
                'segments_count': len(enhanced_segments),
                'transcription_model': self.model_name
            }
        }

        return enhanced_transcript

    def save_transcript(self, transcript: Dict[str, Any], output_path: str) -> bool:
        """Sauvegarde la transcription en JSON"""
        try:
            ensure_directory_exists(str(Path(output_path).parent))

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)

            logger.info(f"Transcription sauvegardée: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False

    def load_transcript(self, transcript_path: str) -> Optional[Dict[str, Any]]:
        """Charge une transcription depuis un fichier JSON"""
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = json.load(f)

            logger.info(f"Transcription chargée: {transcript_path}")
            return transcript

        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            return None

    def transcribe(self, audio_path: str, save_path: str = None) -> Dict[str, Any]:
        """
        Transcription complète d'un fichier audio avec gestion des segments longs
        """
        logger.info(f"Début de la transcription: {audio_path}")
        start_time = time.time()

        try:
            # Charger le modèle si nécessaire
            if not self.model:
                if not self.load_model():
                    raise RuntimeError("Impossible de charger le modèle Whisper")

            # Définir le fichier de sauvegarde
            if not save_path:
                save_path = Config.get_temp_transcript_file(audio_path)

            # Vérifier si une transcription existe déjà
            if Path(save_path).exists():
                logger.info("Transcription existante trouvée, chargement...")
                existing = self.load_transcript(save_path)
                if existing:
                    return existing

            # Diviser l'audio en segments si nécessaire
            audio_segments = self.split_audio_into_segments(audio_path)

            # Transcrire chaque segment
            segment_results = []

            for i, segment_info in enumerate(audio_segments):
                logger.info(f"Transcription segment {i+1}/{len(audio_segments)}")

                result = self.transcribe_segment(
                    segment_info['segment_path'],
                    segment_info['start_time'],
                    segment_info['end_time']
                )

                segment_results.append(result)

            # Fusionner les résultats
            if len(segment_results) > 1:
                merged_transcript = self.merge_transcription_results(segment_results)
            else:
                merged_transcript = segment_results[0]

            # Enrichir avec des métadonnées
            final_transcript = self.enhance_transcript_with_metadata(merged_transcript)

            # Sauvegarder
            self.save_transcript(final_transcript, save_path)

            total_time = time.time() - start_time
            logger.info(f"Transcription terminée en {total_time:.2f}s")

            return final_transcript

        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {e}")
            raise

    def export_transcript_text(self, transcript: Dict[str, Any], output_path: str) -> bool:
        """Exporte la transcription en format texte simple"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Transcription - {transcript['metadata']['transcription_model']}\n")
                f.write(f"Durée: {transcript['metadata']['total_duration']:.2f}s\n")
                f.write(f"Mots: {transcript['metadata']['total_words']}\n")
                f.write("=" * 50 + "\n\n")

                for segment in transcript['segments']:
                    timestamp = f"[{segment['start']:.2f}s -> {segment['end']:.2f}s]"
                    f.write(f"{timestamp} {segment['text']}\n")

            logger.info(f"Transcription texte exportée: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'export texte: {e}")
            return False

    def export_transcript_srt(self, transcript: Dict[str, Any], output_path: str) -> bool:
        """Exporte la transcription au format SRT (sous-titres)"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(transcript['segments'], 1):
                    start_time = self._seconds_to_srt_time(segment['start'])
                    end_time = self._seconds_to_srt_time(segment['end'])

                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text'].strip()}\n\n")

            logger.info(f"Transcription SRT exportée: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'export SRT: {e}")
            return False

    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convertit les secondes au format timestamp SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"