# -*- coding: utf-8 -*-

import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional
import ffmpeg

from config import Config
from utils.file_manager import ensure_directory_exists, get_safe_filename

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Gestionnaire de traitement vidéo avec FFmpeg"""

    def __init__(self):
        self.temp_files = []  # Suivi des fichiers temporaires

    def __del__(self):
        """Nettoyage des fichiers temporaires"""
        self.cleanup_temp_files()

    def cleanup_temp_files(self):
        """Supprime les fichiers temporaires créés"""
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
                    logger.debug(f"Fichier temporaire supprimé: {temp_file}")
            except Exception as e:
                logger.warning(f"Impossible de supprimer {temp_file}: {e}")
        self.temp_files.clear()

    def validate_ffmpeg(self) -> bool:
        """Vérifie que FFmpeg est disponible"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("FFmpeg disponible")
                return True
            else:
                logger.error("FFmpeg non disponible ou dysfonctionnel")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"FFmpeg non trouvé: {e}")
            return False

    def get_video_info(self, video_path: str) -> dict:
        """Récupère les informations d'une vidéo"""
        try:
            probe = ffmpeg.probe(video_path)
            video_streams = [s for s in probe['streams'] if s['codec_type'] == 'video']
            audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']

            if not video_streams:
                raise ValueError("Aucun stream vidéo trouvé")

            video_stream = video_streams[0]
            duration = float(probe['format']['duration'])

            info = {
                'duration': duration,
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']),  # Conversion fraction to float
                'codec': video_stream['codec_name'],
                'has_audio': len(audio_streams) > 0,
                'size_bytes': int(probe['format']['size']),
                'bitrate': int(probe['format']['bit_rate']) if 'bit_rate' in probe['format'] else None
            }

            logger.debug(f"Info vidéo {video_path}: {info}")
            return info

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de {video_path}: {e}")
            raise

    def concatenate_mts_files(self, mts_files: List[str]) -> str:
        """Concatène plusieurs fichiers MTS en un seul"""
        if len(mts_files) <= 1:
            return mts_files[0] if mts_files else None

        logger.info(f"Concaténation de {len(mts_files)} fichiers MTS")

        # Créer le fichier de liste pour ffmpeg
        concat_file = Config.TEMP_DIR / "concat_list.txt"
        self.temp_files.append(str(concat_file))

        try:
            with open(concat_file, 'w', encoding='utf-8') as f:
                for mts_file in mts_files:
                    # Échapper les apostrophes pour ffmpeg
                    safe_path = str(Path(mts_file)).replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            # Fichier de sortie
            output_file = Config.TEMP_DIR / "concatenated_video.mp4"
            self.temp_files.append(str(output_file))

            # Commande ffmpeg pour concaténation
            (
                ffmpeg
                .input(str(concat_file), format='concat', safe=0)
                .output(
                    str(output_file),
                    vcodec='copy',
                    acodec='copy'
                )
                .overwrite_output()
                .run(quiet=True)
            )

            logger.info(f"Concaténation terminée: {output_file}")
            return str(output_file)

        except ffmpeg.Error as e:
            logger.error(f"Erreur FFmpeg lors de la concaténation: {e.stderr.decode()}")
            raise ValueError(f"Échec de la concaténation: {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"Erreur lors de la concaténation: {e}")
            raise

    def extract_audio(self, video_path: str) -> str:
        """Extrait la piste audio d'une vidéo"""
        logger.info(f"Extraction audio de: {video_path}")

        try:
            # Fichier de sortie audio
            audio_file = Config.get_temp_audio_file(video_path)
            self.temp_files.append(str(audio_file))

            # Extraction avec ffmpeg
            (
                ffmpeg
                .input(video_path)
                .output(
                    str(audio_file),
                    acodec='pcm_s16le',  # Format WAV non compressé
                    ac=1,  # Mono
                    ar=16000  # 16kHz (optimal pour Whisper)
                )
                .overwrite_output()
                .run(quiet=True)
            )

            logger.info(f"Audio extrait: {audio_file}")
            return str(audio_file)

        except ffmpeg.Error as e:
            logger.error(f"Erreur FFmpeg lors de l'extraction audio: {e.stderr.decode()}")
            raise ValueError(f"Échec de l'extraction audio: {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction audio: {e}")
            raise

    def split_video_by_segments(self, video_path: str, segments: List[dict], output_dir: str) -> List[str]:
        """Découpe une vidéo selon les segments fournis"""
        logger.info(f"Découpage de {video_path} en {len(segments)} segments")

        ensure_directory_exists(output_dir)
        output_files = []

        try:
            for i, segment in enumerate(segments):
                start_time = segment['start_seconds']
                end_time = segment['end_seconds']
                duration = end_time - start_time

                # Nom de fichier sécurisé
                safe_title = get_safe_filename(segment['title'])
                output_filename = f"{i+1:02d}_{safe_title}.{Config.OUTPUT_VIDEO_FORMAT}"
                output_path = Path(output_dir) / output_filename

                logger.debug(f"Segment {i+1}: {start_time}s -> {end_time}s ({duration}s)")

                # Découpe avec ffmpeg
                (
                    ffmpeg
                    .input(video_path, ss=start_time, t=duration)
                    .output(
                        str(output_path),
                        vcodec=Config.OUTPUT_VIDEO_CODEC,
                        acodec=Config.OUTPUT_AUDIO_CODEC,
                        crf=Config.VIDEO_QUALITY,
                        preset='medium'  # Balance qualité/vitesse
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )

                output_files.append(str(output_path))
                logger.info(f"Segment {i+1} créé: {output_path}")

        except ffmpeg.Error as e:
            logger.error(f"Erreur FFmpeg lors du découpage: {e.stderr.decode()}")
            raise ValueError(f"Échec du découpage: {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"Erreur lors du découpage: {e}")
            raise

        logger.info(f"Découpage terminé: {len(output_files)} segments créés")
        return output_files

    def process_video_files(self, video_files: List[str]) -> str:
        """
        Traite une liste de fichiers vidéo:
        - Concatène les fichiers MTS si plusieurs
        - Retourne le chemin du fichier vidéo final
        """
        logger.info(f"Traitement de {len(video_files)} fichiers vidéo")

        if not video_files:
            raise ValueError("Aucun fichier vidéo fourni")

        # Vérifier FFmpeg
        if not self.validate_ffmpeg():
            raise RuntimeError("FFmpeg n'est pas disponible. Veuillez l'installer.")

        # Créer les dossiers temporaires
        ensure_directory_exists(str(Config.TEMP_DIR))

        # Séparer les fichiers MTS des autres
        mts_files = [f for f in video_files if Path(f).suffix.lower() == '.mts']
        other_files = [f for f in video_files if Path(f).suffix.lower() != '.mts']

        if len(mts_files) > 1:
            # Concaténer les fichiers MTS
            logger.info("Concaténation des fichiers MTS détectée")
            concatenated_file = self.concatenate_mts_files(mts_files)

            if other_files:
                logger.warning("Fichiers MTS et autres formats mélangés - seuls les MTS seront traités")

            return concatenated_file

        elif len(mts_files) == 1:
            if other_files:
                logger.warning("Fichiers MTS et autres formats mélangés - seul le MTS sera traité")
            return mts_files[0]

        elif len(other_files) == 1:
            # Un seul fichier non-MTS
            return other_files[0]

        elif len(other_files) > 1:
            # Plusieurs fichiers non-MTS - prendre le premier
            logger.warning(f"Plusieurs fichiers non-MTS fournis - seul {other_files[0]} sera traité")
            return other_files[0]

        else:
            raise ValueError("Aucun fichier vidéo valide trouvé")

    def create_preview_clip(self, video_path: str, start_time: float, duration: float = 30.0) -> str:
        """Crée un extrait de prévisualisation de 30 secondes"""
        logger.info(f"Création d'un aperçu: {start_time}s, durée {duration}s")

        try:
            preview_file = Config.TEMP_DIR / f"preview_{int(start_time)}.mp4"
            self.temp_files.append(str(preview_file))

            (
                ffmpeg
                .input(video_path, ss=start_time, t=duration)
                .output(
                    str(preview_file),
                    vcodec='libx264',
                    acodec='aac',
                    crf=25,  # Qualité plus rapide pour preview
                    preset='ultrafast'
                )
                .overwrite_output()
                .run(quiet=True)
            )

            return str(preview_file)

        except ffmpeg.Error as e:
            logger.error(f"Erreur lors de la création de l'aperçu: {e.stderr.decode()}")
            raise ValueError(f"Échec de création de l'aperçu: {e.stderr.decode()}")

    def get_thumbnail(self, video_path: str, timestamp: float) -> str:
        """Génère une miniature à un timestamp donné"""
        try:
            thumbnail_file = Config.TEMP_DIR / f"thumb_{int(timestamp)}.jpg"
            self.temp_files.append(str(thumbnail_file))

            (
                ffmpeg
                .input(video_path, ss=timestamp)
                .output(str(thumbnail_file), vframes=1, format='image2')
                .overwrite_output()
                .run(quiet=True)
            )

            return str(thumbnail_file)

        except ffmpeg.Error as e:
            logger.error(f"Erreur lors de la génération de miniature: {e.stderr.decode()}")
            raise ValueError(f"Échec de génération de miniature: {e.stderr.decode()}")