# -*- coding: utf-8 -*-

import logging
import os
import threading
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from PyQt5.QtCore import QObject, pyqtSignal

from config import Config
from video.processor import VideoProcessor
from utils.file_manager import ensure_directory_exists, get_safe_filename

logger = logging.getLogger(__name__)


class ExportProgress(QObject):
    """Gestionnaire de progression d'export avec signaux Qt"""

    progress_updated = pyqtSignal(int, str)  # pourcentage, message
    segment_started = pyqtSignal(int, str)   # index, nom du segment
    segment_completed = pyqtSignal(int, str, str)  # index, nom, chemin de sortie
    export_completed = pyqtSignal(list)      # liste des fichiers créés
    error_occurred = pyqtSignal(str)         # message d'erreur


class VideoExporter:
    """Gestionnaire d'export des segments vidéo"""

    def __init__(self):
        self.video_processor = VideoProcessor()
        self.progress = ExportProgress()
        self.is_exporting = False
        self.cancel_requested = False

    def export_segments(self, video_path: str, segments: List[Dict[str, Any]],
                       output_directory: str, progress_callback: Callable = None) -> List[str]:
        """
        Exporte tous les segments vers le dossier spécifié

        Args:
            video_path: Chemin vers la vidéo source
            segments: Liste des segments à exporter
            output_directory: Dossier de destination
            progress_callback: Fonction callback pour les mises à jour de progression

        Returns:
            Liste des chemins des fichiers créés
        """
        logger.info(f"Début de l'export de {len(segments)} segments vers {output_directory}")

        if self.is_exporting:
            raise RuntimeError("Un export est déjà en cours")

        self.is_exporting = True
        self.cancel_requested = False

        try:
            # Créer le dossier de sortie
            ensure_directory_exists(output_directory)

            exported_files = []
            total_segments = len(segments)

            # Connecter le callback si fourni
            if progress_callback:
                self.progress.progress_updated.connect(progress_callback)

            for i, segment in enumerate(segments):
                if self.cancel_requested:
                    logger.info("Export annulé par l'utilisateur")
                    break

                # Progression
                progress_percent = int((i / total_segments) * 100)
                segment_name = segment.get('title', f'Segment {i+1}')

                self.progress.progress_updated.emit(
                    progress_percent,
                    f"Export en cours: {segment_name} ({i+1}/{total_segments})"
                )
                self.progress.segment_started.emit(i, segment_name)

                # Export du segment
                try:
                    output_file = self.export_single_segment(
                        video_path,
                        segment,
                        output_directory,
                        i + 1
                    )

                    if output_file:
                        exported_files.append(output_file)
                        self.progress.segment_completed.emit(i, segment_name, output_file)
                        logger.info(f"Segment exporté: {output_file}")

                except Exception as e:
                    error_msg = f"Erreur lors de l'export du segment {i+1}: {str(e)}"
                    logger.error(error_msg)
                    self.progress.error_occurred.emit(error_msg)
                    continue

            # Export terminé
            if not self.cancel_requested:
                self.progress.progress_updated.emit(100, "Export terminé !")
                self.progress.export_completed.emit(exported_files)
                logger.info(f"Export terminé: {len(exported_files)} fichiers créés")

            return exported_files

        except Exception as e:
            error_msg = f"Erreur générale lors de l'export: {str(e)}"
            logger.error(error_msg)
            self.progress.error_occurred.emit(error_msg)
            raise

        finally:
            self.is_exporting = False

    def export_single_segment(self, video_path: str, segment: Dict[str, Any],
                             output_directory: str, segment_number: int) -> Optional[str]:
        """
        Exporte un segment individuel

        Args:
            video_path: Chemin vers la vidéo source
            segment: Dictionnaire contenant les infos du segment
            output_directory: Dossier de destination
            segment_number: Numéro du segment pour le nommage

        Returns:
            Chemin du fichier créé ou None en cas d'erreur
        """
        try:
            # Générer le nom de fichier
            segment_title = segment.get('title', f'Segment {segment_number}')
            safe_title = get_safe_filename(segment_title)

            filename = f"{segment_number:02d}_{safe_title}.{Config.OUTPUT_VIDEO_FORMAT}"
            output_path = Path(output_directory) / filename

            # Timestamps
            start_time = segment.get('start_seconds', segment.get('start_time', 0))
            end_time = segment.get('end_seconds', segment.get('end_time', 0))

            if start_time >= end_time:
                logger.error(f"Timestamps invalides pour le segment {segment_number}: {start_time} -> {end_time}")
                return None

            # Utiliser VideoProcessor pour découper
            temp_segments = [{
                'title': segment_title,
                'start_seconds': start_time,
                'end_seconds': end_time
            }]

            result_files = self.video_processor.split_video_by_segments(
                video_path,
                temp_segments,
                output_directory
            )

            if result_files:
                # Renommer le fichier si nécessaire
                temp_file = result_files[0]
                if temp_file != str(output_path):
                    Path(temp_file).rename(output_path)

                return str(output_path)

            return None

        except Exception as e:
            logger.error(f"Erreur lors de l'export du segment {segment_number}: {e}")
            return None

    def export_segments_async(self, video_path: str, segments: List[Dict[str, Any]],
                             output_directory: str) -> threading.Thread:
        """
        Lance l'export en arrière-plan dans un thread séparé

        Returns:
            Thread d'export (déjà démarré)
        """
        def export_worker():
            try:
                self.export_segments(video_path, segments, output_directory)
            except Exception as e:
                logger.error(f"Erreur dans le thread d'export: {e}")

        thread = threading.Thread(target=export_worker, daemon=True)
        thread.start()
        return thread

    def cancel_export(self):
        """Annule l'export en cours"""
        if self.is_exporting:
            logger.info("Demande d'annulation de l'export")
            self.cancel_requested = True
        else:
            logger.warning("Aucun export en cours à annuler")

    def estimate_export_time(self, segments: List[Dict[str, Any]]) -> float:
        """
        Estime le temps d'export en secondes

        Args:
            segments: Liste des segments à exporter

        Returns:
            Temps estimé en secondes
        """
        total_duration = sum([
            segment.get('end_seconds', segment.get('end_time', 0)) -
            segment.get('start_seconds', segment.get('start_time', 0))
            for segment in segments
        ])

        # Estimation approximative: 0.1x la durée totale des segments
        # (FFmpeg est généralement rapide pour le découpage)
        estimated_time = total_duration * 0.1

        # Minimum 10 secondes, maximum 30 minutes
        estimated_time = max(10, min(estimated_time, 1800))

        logger.debug(f"Temps d'export estimé: {estimated_time:.2f}s pour {len(segments)} segments")
        return estimated_time

    def get_export_info(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Récupère des informations sur l'export à venir

        Args:
            segments: Liste des segments à exporter

        Returns:
            Dictionnaire avec les informations d'export
        """
        total_duration = sum([
            segment.get('end_seconds', segment.get('end_time', 0)) -
            segment.get('start_seconds', segment.get('start_time', 0))
            for segment in segments
        ])

        estimated_size_mb = total_duration * 2  # ~2MB par minute (estimation approximative)

        info = {
            'segments_count': len(segments),
            'total_duration_seconds': total_duration,
            'total_duration_formatted': self._format_duration(total_duration),
            'estimated_time_seconds': self.estimate_export_time(segments),
            'estimated_time_formatted': self._format_duration(self.estimate_export_time(segments)),
            'estimated_size_mb': estimated_size_mb,
            'estimated_size_formatted': self._format_file_size(estimated_size_mb * 1024 * 1024),
            'output_format': Config.OUTPUT_VIDEO_FORMAT.upper(),
            'video_codec': Config.OUTPUT_VIDEO_CODEC,
            'audio_codec': Config.OUTPUT_AUDIO_CODEC,
            'quality_setting': f"CRF {Config.VIDEO_QUALITY}"
        }

        return info

    def validate_export_settings(self, video_path: str, segments: List[Dict[str, Any]],
                                 output_directory: str) -> tuple[bool, List[str]]:
        """
        Valide les paramètres d'export

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Vérifier le fichier vidéo source
        if not Path(video_path).exists():
            errors.append(f"Fichier vidéo source introuvable: {video_path}")
        elif not Path(video_path).is_file():
            errors.append(f"Le chemin source n'est pas un fichier: {video_path}")

        # Vérifier le dossier de destination
        try:
            ensure_directory_exists(output_directory)
            if not os.access(output_directory, os.W_OK):
                errors.append(f"Impossible d'écrire dans le dossier: {output_directory}")
        except Exception as e:
            errors.append(f"Erreur avec le dossier de destination: {str(e)}")

        # Vérifier les segments
        if not segments:
            errors.append("Aucun segment à exporter")
        else:
            for i, segment in enumerate(segments):
                start_time = segment.get('start_seconds', segment.get('start_time'))
                end_time = segment.get('end_seconds', segment.get('end_time'))

                if start_time is None or end_time is None:
                    errors.append(f"Segment {i+1}: timestamps manquants")
                elif start_time >= end_time:
                    errors.append(f"Segment {i+1}: timestamps invalides ({start_time} -> {end_time})")
                elif end_time - start_time < 1:
                    errors.append(f"Segment {i+1}: trop court ({end_time - start_time:.2f}s)")

        # Vérifier l'espace disque disponible
        try:
            import shutil
            free_space = shutil.disk_usage(output_directory).free
            estimated_size = sum([
                (segment.get('end_seconds', segment.get('end_time', 0)) -
                 segment.get('start_seconds', segment.get('start_time', 0))) * 2 * 1024 * 1024
                for segment in segments
            ])

            if estimated_size > free_space:
                errors.append(f"Espace disque insuffisant (requis: {self._format_file_size(estimated_size)}, disponible: {self._format_file_size(free_space)})")

        except Exception as e:
            logger.warning(f"Impossible de vérifier l'espace disque: {e}")

        return len(errors) == 0, errors

    def _format_duration(self, seconds: float) -> str:
        """Formate une durée en secondes vers un format lisible"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m{secs:02d}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}h{minutes:02d}m{secs:02d}s"

    def _format_file_size(self, bytes_size: float) -> str:
        """Formate une taille de fichier en octets vers un format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"


class BatchExporter:
    """Gestionnaire d'exports multiples ou par lots"""

    def __init__(self):
        self.exporters = []
        self.current_batch = []

    def add_export_job(self, video_path: str, segments: List[Dict[str, Any]],
                      output_directory: str, job_name: str = None) -> int:
        """
        Ajoute un travail d'export à la file

        Returns:
            ID du travail ajouté
        """
        job_id = len(self.current_batch)
        job = {
            'id': job_id,
            'name': job_name or f"Export {job_id + 1}",
            'video_path': video_path,
            'segments': segments,
            'output_directory': output_directory,
            'status': 'pending',
            'created_files': [],
            'error_message': None
        }

        self.current_batch.append(job)
        logger.info(f"Travail d'export ajouté: {job['name']} ({len(segments)} segments)")
        return job_id

    def process_batch(self, max_concurrent: int = 1) -> Dict[str, Any]:
        """
        Traite tous les travaux d'export de la file

        Args:
            max_concurrent: Nombre maximum d'exports simultanés

        Returns:
            Résumé de l'exécution du lot
        """
        logger.info(f"Traitement du lot: {len(self.current_batch)} travaux")

        if not self.current_batch:
            return {'status': 'no_jobs', 'results': []}

        results = []

        for job in self.current_batch:
            try:
                job['status'] = 'processing'
                logger.info(f"Traitement du travail: {job['name']}")

                exporter = VideoExporter()
                exported_files = exporter.export_segments(
                    job['video_path'],
                    job['segments'],
                    job['output_directory']
                )

                job['created_files'] = exported_files
                job['status'] = 'completed'

                results.append({
                    'job_id': job['id'],
                    'name': job['name'],
                    'status': 'success',
                    'files_created': len(exported_files),
                    'files': exported_files
                })

            except Exception as e:
                job['status'] = 'failed'
                job['error_message'] = str(e)

                results.append({
                    'job_id': job['id'],
                    'name': job['name'],
                    'status': 'failed',
                    'error': str(e)
                })

                logger.error(f"Échec du travail {job['name']}: {e}")

        # Statistiques finales
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        total_files = sum(r.get('files_created', 0) for r in results)

        summary = {
            'status': 'completed',
            'total_jobs': len(self.current_batch),
            'successful_jobs': successful,
            'failed_jobs': failed,
            'total_files_created': total_files,
            'results': results
        }

        logger.info(f"Lot terminé: {successful}/{len(results)} réussis, {total_files} fichiers créés")

        # Nettoyer la file après traitement
        self.current_batch = []

        return summary