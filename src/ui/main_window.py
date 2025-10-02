# -*- coding: utf-8 -*-

import sys
import logging
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QProgressBar, QTextEdit, QGroupBox,
    QListWidget, QListWidgetItem, QSplitter, QMessageBox, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

from config import Config
from utils.file_manager import FileValidator, ProjectState
from video.processor import VideoProcessor
from transcription.whisper_transcriber import WhisperTranscriber
from ai_analysis.analyzer import AIAnalyzer
from export.exporter import VideoExporter
from ui.segment_editor import SegmentEditDialog, SegmentListManager

logger = logging.getLogger(__name__)


class ProcessingThread(QThread):
    """Thread pour le traitement vidéo en arrière-plan"""

    progress_updated = pyqtSignal(int, str)
    stage_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    processing_complete = pyqtSignal(dict)

    def __init__(self, video_files, parent=None):
        super().__init__(parent)
        self.video_files = video_files
        self.processor = VideoProcessor()
        self.transcriber = WhisperTranscriber()
        self.analyzer = AIAnalyzer()

    def run(self):
        try:
            # Étape 1: Traitement vidéo
            self.stage_changed.emit("Traitement des fichiers vidéo...")
            self.progress_updated.emit(10, "Concaténation des fichiers MTS...")

            combined_video = self.processor.process_video_files(self.video_files)

            # Étape 2: Extraction audio
            self.progress_updated.emit(25, "Extraction de la piste audio...")
            audio_file = self.processor.extract_audio(combined_video)

            # Étape 3: Transcription
            self.stage_changed.emit("Transcription en cours...")
            self.progress_updated.emit(40, "Transcription avec Whisper...")

            transcript = self.transcriber.transcribe(audio_file)

            # Étape 3.5: Export de la transcription en texte
            self.progress_updated.emit(60, "Export de la transcription...")

            # Créer un nom de fichier unique basé sur la vidéo source
            from pathlib import Path
            video_base_name = Path(combined_video).stem
            transcript_dir = Config.OUTPUT_DIR / "transcriptions"
            transcript_dir.mkdir(exist_ok=True)

            # Export en texte
            txt_path = transcript_dir / f"{video_base_name}_transcription.txt"
            self.transcriber.export_transcript_text(transcript, str(txt_path))

            # Export en JSON (déjà sauvegardé par transcribe(), mais copions aussi)
            import shutil
            json_src = Config.get_temp_transcript_file(audio_file)
            json_dst = transcript_dir / f"{video_base_name}_transcription.json"
            if Path(json_src).exists():
                shutil.copy2(json_src, json_dst)

            # Étape 4: Analyse IA
            self.stage_changed.emit("Analyse intelligente...")
            self.progress_updated.emit(70, "Analyse des thèmes et découpage...")

            segments = self.analyzer.analyze_transcript(transcript)

            # Finalisation
            self.progress_updated.emit(100, "Traitement terminé !")

            result = {
                'video_file': combined_video,
                'audio_file': audio_file,
                'transcript': transcript,
                'transcript_txt': str(txt_path),
                'transcript_json': str(json_dst),
                'source_videos': self.video_files,  # Garder la trace des vidéos sources
                'segments': segments
            }

            self.processing_complete.emit(result)

        except Exception as e:
            logger.error(f"Erreur dans ProcessingThread: {e}")
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""

    def __init__(self):
        super().__init__()
        self.project_state = ProjectState()
        self.processing_thread = None
        self.selected_files = []
        self.output_folder = str(Config.OUTPUT_DIR)  # Dossier de sortie par défaut
        self.current_result = None
        self.video_exporter = VideoExporter()
        self.segment_manager = None

        self.init_ui()
        self.setup_autosave()
        self.check_for_saved_state()

    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Découpeur Vidéo Intelligent v1.0")
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        self.setMinimumSize(900, 700)

        # Style moderne
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #1976d2;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #fafafa;
            }
        """)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # En-tête avec titre
        self.create_header(main_layout)

        # Zone de sélection des fichiers
        self.create_file_selection_area(main_layout)

        # Zone de dossier de sortie
        self.create_output_folder_area(main_layout)

        # Zone de progression
        self.create_progress_area(main_layout)

        # Zone de résultats (initialement cachée)
        self.create_results_area(main_layout)

        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pret a commencer")
        self.status_bar.setStyleSheet("QStatusBar { background-color: #e8f5e9; padding: 5px; }")

    def create_header(self, layout):
        """Crée la zone d'en-tête"""
        header_group = QGroupBox()
        header_layout = QVBoxLayout(header_group)

        title_label = QLabel("Découpeur Vidéo Intelligent")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)

        subtitle_label = QLabel("Analysez vos interviews et créez automatiquement des extraits thématiques")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: gray; font-size: 12px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_group)

    def create_file_selection_area(self, layout):
        """Crée la zone de sélection des fichiers"""
        file_group = QGroupBox("1. Sélection des fichiers vidéo")
        file_layout = QVBoxLayout(file_group)

        # Boutons de sélection
        button_layout = QHBoxLayout()

        self.select_files_btn = QPushButton("Sélectionner les fichiers vidéo")
        self.select_files_btn.clicked.connect(self.select_video_files)
        self.select_files_btn.setMinimumHeight(40)

        self.clear_files_btn = QPushButton("Effacer la sélection")
        self.clear_files_btn.clicked.connect(self.clear_selection)
        self.clear_files_btn.setEnabled(False)

        button_layout.addWidget(self.select_files_btn)
        button_layout.addWidget(self.clear_files_btn)
        button_layout.addStretch()

        # Liste des fichiers sélectionnés
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(150)

        # Bouton de démarrage
        self.start_btn = QPushButton("Démarrer l'analyse")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        file_layout.addLayout(button_layout)
        file_layout.addWidget(QLabel("Fichiers sélectionnés:"))
        file_layout.addWidget(self.files_list)
        file_layout.addWidget(self.start_btn)

        layout.addWidget(file_group)

    def create_output_folder_area(self, layout):
        """Crée la zone de sélection du dossier de sortie"""
        output_group = QGroupBox("2. Dossier de destination des extraits")
        output_layout = QHBoxLayout(output_group)

        # Label du dossier actuel
        self.output_folder_label = QLabel(self.output_folder)
        self.output_folder_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #d0d0d0;
            }
        """)

        # Bouton pour changer le dossier
        self.change_output_btn = QPushButton("📁 Changer le dossier")
        self.change_output_btn.clicked.connect(self.select_output_folder)
        self.change_output_btn.setMinimumHeight(40)
        self.change_output_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        output_layout.addWidget(QLabel("📂 Dossier actuel:"))
        output_layout.addWidget(self.output_folder_label, 1)
        output_layout.addWidget(self.change_output_btn)

        layout.addWidget(output_group)

    def select_output_folder(self):
        """Ouvre le dialogue de sélection du dossier de sortie"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier de destination",
            self.output_folder
        )

        if folder:
            self.output_folder = folder
            self.output_folder_label.setText(folder)
            self.status_bar.showMessage(f"✓ Dossier de sortie: {folder}")
            logger.info(f"Dossier de sortie changé: {folder}")

    def create_progress_area(self, layout):
        """Crée la zone de progression"""
        self.progress_group = QGroupBox("3. Progression du traitement")
        progress_layout = QVBoxLayout(self.progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)

        self.stage_label = QLabel("")
        self.stage_label.setVisible(False)
        stage_font = QFont()
        stage_font.setBold(True)
        self.stage_label.setFont(stage_font)

        progress_layout.addWidget(self.stage_label)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(self.progress_group)
        self.progress_group.setVisible(False)

    def create_results_area(self, layout):
        """Crée la zone d'affichage des résultats"""
        self.results_group = QGroupBox("4. Extraits proposés")
        results_layout = QVBoxLayout(self.results_group)

        # Splitter pour diviser la zone en deux
        splitter = QSplitter(Qt.Horizontal)

        # Liste des extraits à gauche
        self.segments_list = QListWidget()
        self.segments_list.itemClicked.connect(self.on_segment_selected)
        self.segments_list.itemDoubleClicked.connect(self.edit_selected_segment)

        # Gestionnaire de segments
        self.segment_manager = SegmentListManager(self.segments_list)

        # Zone de détails à droite
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        self.segment_details = QTextEdit()
        self.segment_details.setReadOnly(True)
        self.segment_details.setMaximumHeight(200)

        # Boutons d'action
        action_layout = QHBoxLayout()

        self.edit_segment_btn = QPushButton("Modifier")
        self.delete_segment_btn = QPushButton("Supprimer")
        self.preview_btn = QPushButton("Prévisualiser")
        self.export_all_btn = QPushButton("Exporter tous les extraits")

        self.edit_segment_btn.clicked.connect(self.edit_selected_segment)
        self.delete_segment_btn.clicked.connect(self.delete_selected_segment)
        self.preview_btn.clicked.connect(self.preview_selected_segment)
        self.export_all_btn.clicked.connect(self.export_all_segments)

        action_layout.addWidget(self.edit_segment_btn)
        action_layout.addWidget(self.delete_segment_btn)
        action_layout.addWidget(self.preview_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.export_all_btn)

        details_layout.addWidget(QLabel("Détails de l'extrait:"))
        details_layout.addWidget(self.segment_details)
        details_layout.addLayout(action_layout)

        splitter.addWidget(self.segments_list)
        splitter.addWidget(details_widget)
        splitter.setSizes([300, 400])

        results_layout.addWidget(splitter)

        layout.addWidget(self.results_group)
        self.results_group.setVisible(False)

    def setup_autosave(self):
        """Configure la sauvegarde automatique"""
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave_project)
        self.autosave_timer.start(Config.AUTOSAVE_INTERVAL * 1000)  # Convert to ms

    def check_for_saved_state(self):
        """Vérifie s'il existe un état sauvegardé"""
        if self.project_state.has_saved_state():
            reply = QMessageBox.question(
                self,
                "Projet sauvegardé trouvé",
                "Un projet en cours a été trouvé. Voulez-vous le restaurer ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.restore_project_state()

    def select_video_files(self):
        """Ouvre le dialogue de sélection de fichiers"""
        file_filter = "Fichiers vidéo ("
        file_filter += " ".join(f"*{ext}" for ext in Config.SUPPORTED_VIDEO_FORMATS)
        file_filter += ");;Tous les fichiers (*)"

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner les fichiers vidéo",
            "",
            file_filter
        )

        if files:
            valid_files, errors = FileValidator.validate_video_files(files)

            if errors:
                error_msg = "Erreurs trouvées:\n" + "\n".join(errors)
                QMessageBox.warning(self, "Fichiers invalides", error_msg)

            if valid_files:
                self.selected_files = valid_files
                self.update_files_display()
                self.start_btn.setEnabled(True)
                self.clear_files_btn.setEnabled(True)

    def clear_selection(self):
        """Efface la sélection de fichiers"""
        self.selected_files = []
        self.files_list.clear()
        self.start_btn.setEnabled(False)
        self.clear_files_btn.setEnabled(False)

    def update_files_display(self):
        """Met à jour l'affichage de la liste des fichiers"""
        self.files_list.clear()
        for file_path in self.selected_files:
            item = QListWidgetItem(Path(file_path).name)
            item.setToolTip(file_path)
            self.files_list.addItem(item)

    def start_processing(self):
        """Démarre le traitement des vidéos"""
        if not self.selected_files:
            return

        # Désactiver les contrôles
        self.start_btn.setEnabled(False)
        self.select_files_btn.setEnabled(False)

        # Afficher la zone de progression
        self.progress_group.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.stage_label.setVisible(True)

        # Lancer le thread de traitement
        self.processing_thread = ProcessingThread(self.selected_files, self)
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.stage_changed.connect(self.update_stage)
        self.processing_thread.error_occurred.connect(self.handle_processing_error)
        self.processing_thread.processing_complete.connect(self.handle_processing_complete)
        self.processing_thread.start()

        logger.info(f"Traitement démarré pour {len(self.selected_files)} fichiers")

    def update_progress(self, value, message):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        self.status_bar.showMessage(message)

    def update_stage(self, stage):
        """Met à jour l'étape actuelle"""
        self.stage_label.setText(stage)

    def handle_processing_error(self, error_message):
        """Gère les erreurs de traitement"""
        logger.error(f"Erreur de traitement: {error_message}")

        QMessageBox.critical(
            self,
            "Erreur de traitement",
            f"Une erreur s'est produite:\n{error_message}"
        )

        self.reset_ui_after_processing()

    def handle_processing_complete(self, result):
        """Gère la fin du traitement"""
        logger.info("Traitement terminé avec succès")

        self.current_result = result
        self.display_results(result['segments'])
        self.reset_ui_after_processing()

        # Afficher la zone de résultats
        self.results_group.setVisible(True)

        # Afficher un message avec les infos de la transcription
        transcript_info = f"""Traitement termine avec succes !

Resultats:
  - {len(result['segments'])} segments video crees
  - Transcription complete disponible

Fichiers de transcription:
  - Texte: {Path(result['transcript_txt']).name}
  - JSON: {Path(result['transcript_json']).name}

Emplacement: {Path(result['transcript_txt']).parent}

Vous pouvez maintenant previsualiser les segments et les exporter."""

        QMessageBox.information(self, "Traitement termine", transcript_info)

        # Sauvegarder l'état
        self.autosave_project()

    def reset_ui_after_processing(self):
        """Remet l'interface dans son état initial après traitement"""
        self.start_btn.setEnabled(True)
        self.select_files_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.stage_label.setVisible(False)
        self.progress_group.setVisible(False)

    def display_results(self, segments):
        """Affiche les résultats de l'analyse"""
        if self.segment_manager:
            video_duration = self.current_result.get('metadata', {}).get('total_duration') if self.current_result else None
            self.segment_manager.set_segments(segments, video_duration)

    def on_segment_selected(self, item):
        """Gère la sélection d'un segment"""
        if self.segment_manager:
            selection = self.segment_manager.get_selected_segment()
            if selection:
                index, segment = selection
                details = f"""Titre: {segment['title']}
Durée: {segment['duration']}
Début: {segment.get('start_time', segment.get('start_seconds', 0)):.2f}s
Fin: {segment.get('end_time', segment.get('end_seconds', 0)):.2f}s

Résumé:
{segment.get('summary', 'Aucun résumé disponible')}

Mots-clés: {', '.join(segment.get('keywords', []))}
Importance: {segment.get('importance', 3)}/5"""

                self.segment_details.setText(details)

    def edit_selected_segment(self):
        """Édite le segment sélectionné"""
        if self.segment_manager:
            selection = self.segment_manager.get_selected_segment()
            if selection:
                index, segment = selection
                self.segment_manager.edit_segment(index)
                # Rafraîchir l'affichage des détails
                self.on_segment_selected(self.segments_list.currentItem())

    def delete_selected_segment(self):
        """Supprime le segment sélectionné"""
        if self.segment_manager:
            selection = self.segment_manager.get_selected_segment()
            if selection:
                index, segment = selection
                self.segment_manager.delete_segment(index)
                # Clear les détails si plus de segments
                if not self.segment_manager.get_all_segments():
                    self.segment_details.clear()

    def preview_selected_segment(self):
        """Prévisualise le segment sélectionné"""
        if not self.current_result or not self.segment_manager:
            QMessageBox.warning(self, "Prévisualisation impossible", "Aucun résultat disponible")
            return

        selection = self.segment_manager.get_selected_segment()
        if not selection:
            QMessageBox.warning(self, "Previsualisation impossible", "Aucun segment selectionne")
            return

        # Déstructurer le tuple (index, segment)
        index, selected_segment = selection

        video_file = self.current_result.get('video_file')
        if not video_file or not Path(video_file).exists():
            QMessageBox.warning(self, "Erreur", "Fichier video source introuvable")
            return

        try:
            # Créer un aperçu temporaire du segment
            from video.processor import VideoProcessor
            processor = VideoProcessor()

            start_time = selected_segment['start_seconds']
            duration = min(30.0, selected_segment['end_seconds'] - start_time)  # Max 30s de prévisualisation

            self.statusBar().showMessage(f"Création de l'aperçu ({duration:.0f}s)...")
            QMessageBox.information(
                self,
                "Prévisualisation",
                f"Création d'un aperçu de {duration:.0f} secondes du segment '{selected_segment['title']}'...\n\n"
                f"L'aperçu s'ouvrira dans votre lecteur vidéo par défaut."
            )

            preview_file = processor.create_preview_clip(video_file, start_time, duration)

            # Ouvrir dans le lecteur par défaut
            import subprocess
            import platform

            if platform.system() == 'Windows':
                import os
                os.startfile(preview_file)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', preview_file])
            else:  # Linux
                subprocess.run(['xdg-open', preview_file])

            self.statusBar().showMessage(f"Aperçu ouvert: {selected_segment['title']}", 5000)

        except Exception as e:
            logger.error(f"Erreur lors de la prévisualisation: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de créer l'aperçu:\n{str(e)}")

    def export_all_segments(self):
        """Exporte tous les segments"""
        if not self.current_result or not self.segment_manager:
            QMessageBox.warning(self, "Export impossible", "Aucun résultat à exporter")
            return

        segments = self.segment_manager.get_all_segments()
        if not segments:
            QMessageBox.warning(self, "Export impossible", "Aucun segment à exporter")
            return

        # Utiliser le dossier de sortie sélectionné
        output_dir = self.output_folder

        if output_dir:
            try:
                # Valider les paramètres d'export
                video_file = self.current_result.get('video_file')
                if not video_file:
                    QMessageBox.critical(self, "Erreur", "Fichier vidéo source introuvable")
                    return

                is_valid, errors = self.video_exporter.validate_export_settings(
                    video_file, segments, output_dir
                )

                if not is_valid:
                    error_msg = "Erreurs de validation:\n" + "\n".join(errors)
                    QMessageBox.warning(self, "Export impossible", error_msg)
                    return

                # Afficher les informations d'export
                export_info = self.video_exporter.get_export_info(segments)
                info_msg = f"""Export de {export_info['segments_count']} segments

Durée totale: {export_info['total_duration_formatted']}
Temps estimé: {export_info['estimated_time_formatted']}
Taille estimée: {export_info['estimated_size_formatted']}
Format: {export_info['output_format']}

Continuer ?"""

                reply = QMessageBox.question(self, "Confirmer l'export", info_msg)
                if reply != QMessageBox.Yes:
                    return

                # Connecter les signaux de progression
                self.video_exporter.progress.progress_updated.connect(self.update_export_progress)
                self.video_exporter.progress.export_completed.connect(self.on_export_completed)
                self.video_exporter.progress.error_occurred.connect(self.on_export_error)

                # Lancer l'export en arrière-plan
                self.export_thread = self.video_exporter.export_segments_async(
                    video_file, segments, output_dir
                )

                # Afficher la progression
                self.show_export_progress()

            except Exception as e:
                logger.error(f"Erreur lors de l'export: {e}")
                QMessageBox.critical(self, "Erreur d'export", f"Erreur inattendue: {str(e)}")

    def show_export_progress(self):
        """Affiche la progression d'export"""
        # Réutiliser la zone de progression existante
        self.progress_group.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.stage_label.setVisible(True)

        self.stage_label.setText("Export des segments en cours...")
        self.export_all_btn.setEnabled(False)

    def update_export_progress(self, percent, message):
        """Met à jour la progression d'export"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
        self.status_bar.showMessage(message)

    def on_export_completed(self, exported_files):
        """Gère la fin de l'export"""
        self.progress_group.setVisible(False)
        self.export_all_btn.setEnabled(True)

        QMessageBox.information(
            self,
            "Export terminé",
            f"Export réussi !\n{len(exported_files)} fichiers créés dans le dossier de destination."
        )

        logger.info(f"Export terminé: {len(exported_files)} fichiers créés")

    def on_export_error(self, error_message):
        """Gère les erreurs d'export"""
        self.progress_group.setVisible(False)
        self.export_all_btn.setEnabled(True)

        QMessageBox.critical(
            self,
            "Erreur d'export",
            f"Une erreur s'est produite lors de l'export:\n{error_message}"
        )

        logger.error(f"Erreur d'export: {error_message}")

    def autosave_project(self):
        """Sauvegarde automatique du projet"""
        if self.current_result:
            state_data = {
                'selected_files': self.selected_files,
                'result': self.current_result,
                'timestamp': str(time.time())
            }
            self.project_state.save_state(state_data)

    def restore_project_state(self):
        """Restaure l'état du projet"""
        state = self.project_state.load_state()
        if state:
            if 'selected_files' in state:
                self.selected_files = state['selected_files']
                self.update_files_display()
                self.start_btn.setEnabled(True)
                self.clear_files_btn.setEnabled(True)

            if 'result' in state:
                self.current_result = state['result']
                if 'segments' in self.current_result:
                    self.display_results(self.current_result['segments'])
                    self.results_group.setVisible(True)

    def closeEvent(self, event):
        """Gère la fermeture de l'application"""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Traitement en cours",
                "Un traitement est en cours. Voulez-vous vraiment quitter ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

            self.processing_thread.terminate()
            self.processing_thread.wait()

        # Sauvegarder avant de fermer
        if self.current_result:
            self.autosave_project()

        event.accept()