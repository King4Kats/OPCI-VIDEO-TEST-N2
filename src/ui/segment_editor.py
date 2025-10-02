# -*- coding: utf-8 -*-

import logging
from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QGroupBox,
    QSlider, QCheckBox, QListWidget, QListWidgetItem, QMessageBox,
    QTabWidget, QWidget, QFormLayout, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap

logger = logging.getLogger(__name__)


class TimeSpinBox(QDoubleSpinBox):
    """SpinBox spécialisé pour les timestamps (MM:SS.ss)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0.0, 99999.99)  # ~27 heures max
        self.setDecimals(2)
        self.setSingleStep(1.0)
        self.setSuffix(" s")

    def set_time_value(self, seconds: float):
        """Définit la valeur en secondes"""
        self.setValue(seconds)

    def get_time_value(self) -> float:
        """Récupère la valeur en secondes"""
        return self.value()


class SegmentValidator:
    """Validateur pour les segments édités"""

    @staticmethod
    def validate_segment(segment: Dict[str, Any], video_duration: float = None) -> tuple[bool, List[str]]:
        """
        Valide un segment
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        # Vérifier les timestamps
        start_time = segment.get('start_seconds', segment.get('start_time', 0))
        end_time = segment.get('end_seconds', segment.get('end_time', 0))

        if start_time >= end_time:
            errors.append("L'heure de fin doit être supérieure à l'heure de début")

        if end_time - start_time < 5:  # Minimum 5 secondes
            errors.append("Le segment doit durer au moins 5 secondes")

        if start_time < 0:
            errors.append("L'heure de début ne peut pas être négative")

        if video_duration and end_time > video_duration:
            errors.append(f"L'heure de fin ne peut pas dépasser la durée de la vidéo ({video_duration:.2f}s)")

        # Vérifier le titre
        title = segment.get('title', '').strip()
        if not title:
            errors.append("Le titre ne peut pas être vide")
        elif len(title) > 100:
            errors.append("Le titre ne peut pas dépasser 100 caractères")

        return len(errors) == 0, errors


class SegmentEditDialog(QDialog):
    """Dialogue d'édition d'un segment individuel"""

    segment_updated = pyqtSignal(dict)

    def __init__(self, segment: Dict[str, Any], video_duration: float = None, parent=None):
        super().__init__(parent)
        self.original_segment = segment.copy()
        self.current_segment = segment.copy()
        self.video_duration = video_duration

        self.init_ui()
        self.load_segment_data()

    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Édition du segment")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Onglets
        tabs = QTabWidget()

        # Onglet principal
        main_tab = self.create_main_tab()
        tabs.addTab(main_tab, "Informations")

        # Onglet timing
        timing_tab = self.create_timing_tab()
        tabs.addTab(timing_tab, "Timing")

        # Onglet avancé
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, "Avancé")

        layout.addWidget(tabs)

        # Boutons
        button_layout = QHBoxLayout()

        self.preview_btn = QPushButton("Prévisualiser")
        self.preview_btn.clicked.connect(self.preview_segment)

        self.reset_btn = QPushButton("Réinitialiser")
        self.reset_btn.clicked.connect(self.reset_to_original)

        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)

        self.apply_btn = QPushButton("Appliquer")
        self.apply_btn.clicked.connect(self.apply_changes)
        self.apply_btn.setDefault(True)

        button_layout.addWidget(self.preview_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

    def create_main_tab(self) -> QWidget:
        """Crée l'onglet principal d'édition"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Titre
        self.title_edit = QLineEdit()
        self.title_edit.setMaxLength(100)
        self.title_edit.textChanged.connect(self.on_field_changed)
        layout.addRow("Titre:", self.title_edit)

        # Description/Résumé
        self.summary_edit = QTextEdit()
        self.summary_edit.setMaximumHeight(100)
        self.summary_edit.textChanged.connect(self.on_field_changed)
        layout.addRow("Résumé:", self.summary_edit)

        # Mots-clés
        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("Séparer les mots-clés par des virgules")
        self.keywords_edit.textChanged.connect(self.on_field_changed)
        layout.addRow("Mots-clés:", self.keywords_edit)

        # Importance
        self.importance_spin = QSpinBox()
        self.importance_spin.setRange(1, 5)
        self.importance_spin.valueChanged.connect(self.on_field_changed)
        layout.addRow("Importance (1-5):", self.importance_spin)

        return widget

    def create_timing_tab(self) -> QWidget:
        """Crée l'onglet de gestion du timing"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Groupe timing principal
        timing_group = QGroupBox("Timestamps")
        timing_layout = QFormLayout(timing_group)

        # Heure de début
        self.start_time_spin = TimeSpinBox()
        self.start_time_spin.valueChanged.connect(self.on_timing_changed)
        timing_layout.addRow("Début:", self.start_time_spin)

        # Heure de fin
        self.end_time_spin = TimeSpinBox()
        self.end_time_spin.valueChanged.connect(self.on_timing_changed)
        timing_layout.addRow("Fin:", self.end_time_spin)

        # Durée (calculée automatiquement)
        self.duration_label = QLabel()
        self.duration_label.setStyleSheet("font-weight: bold;")
        timing_layout.addRow("Durée:", self.duration_label)

        layout.addWidget(timing_group)

        # Groupe d'ajustement fin
        adjust_group = QGroupBox("Ajustement fin")
        adjust_layout = QVBoxLayout(adjust_group)

        # Boutons d'ajustement rapide
        quick_adjust_layout = QHBoxLayout()

        adjust_buttons = [
            ("-10s", -10), ("-5s", -5), ("-1s", -1),
            ("+1s", 1), ("+5s", 5), ("+10s", 10)
        ]

        for text, delta in adjust_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, d=delta: self.adjust_timing(d))
            quick_adjust_layout.addWidget(btn)

        adjust_layout.addLayout(quick_adjust_layout)

        # Sliders pour ajustement précis
        start_slider_layout = QHBoxLayout()
        start_slider_layout.addWidget(QLabel("Début:"))
        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setRange(0, int(self.video_duration * 100) if self.video_duration else 3600000)
        self.start_slider.valueChanged.connect(self.on_start_slider_changed)
        start_slider_layout.addWidget(self.start_slider)
        adjust_layout.addLayout(start_slider_layout)

        end_slider_layout = QHBoxLayout()
        end_slider_layout.addWidget(QLabel("Fin:"))
        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setRange(0, int(self.video_duration * 100) if self.video_duration else 3600000)
        self.end_slider.valueChanged.connect(self.on_end_slider_changed)
        end_slider_layout.addWidget(self.end_slider)
        adjust_layout.addLayout(end_slider_layout)

        layout.addWidget(adjust_group)

        # Validation
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        layout.addStretch()
        return widget

    def create_advanced_tab(self) -> QWidget:
        """Crée l'onglet avancé"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Options avancées
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)

        # Seuil de confiance
        self.confidence_spin = QSpinBox()
        self.confidence_spin.setRange(1, 5)
        self.confidence_spin.valueChanged.connect(self.on_field_changed)
        options_layout.addRow("Confiance (1-5):", self.confidence_spin)

        # Basé sur thème
        self.theme_based_check = QCheckBox()
        self.theme_based_check.stateChanged.connect(self.on_field_changed)
        options_layout.addRow("Basé sur l'analyse IA:", self.theme_based_check)

        layout.addWidget(options_group)

        # Informations techniques
        info_group = QGroupBox("Informations techniques")
        info_layout = QFormLayout(info_group)

        self.tech_info_label = QLabel()
        self.tech_info_label.setWordWrap(True)
        self.tech_info_label.setStyleSheet("color: gray; font-size: 10px;")
        info_layout.addRow(self.tech_info_label)

        layout.addWidget(info_group)

        layout.addStretch()
        return widget

    def load_segment_data(self):
        """Charge les données du segment dans l'interface"""
        # Onglet principal
        self.title_edit.setText(self.current_segment.get('title', ''))
        self.summary_edit.setText(self.current_segment.get('summary', ''))

        keywords = self.current_segment.get('keywords', [])
        self.keywords_edit.setText(', '.join(keywords) if keywords else '')

        self.importance_spin.setValue(self.current_segment.get('importance', 3))

        # Onglet timing
        start_time = self.current_segment.get('start_seconds', self.current_segment.get('start_time', 0))
        end_time = self.current_segment.get('end_seconds', self.current_segment.get('end_time', 0))

        self.start_time_spin.set_time_value(start_time)
        self.end_time_spin.set_time_value(end_time)

        self.start_slider.setValue(int(start_time * 100))
        self.end_slider.setValue(int(end_time * 100))

        # Onglet avancé
        self.confidence_spin.setValue(self.current_segment.get('confidence', 3))
        self.theme_based_check.setChecked(self.current_segment.get('theme_based', False))

        self.update_duration_display()
        self.update_tech_info()
        self.validate_current_segment()

    def on_field_changed(self):
        """Appelé lors de la modification d'un champ"""
        self.update_current_segment()
        self.validate_current_segment()

    def on_timing_changed(self):
        """Appelé lors de la modification des timestamps"""
        # Mettre à jour les sliders
        start_time = self.start_time_spin.get_time_value()
        end_time = self.end_time_spin.get_time_value()

        self.start_slider.blockSignals(True)
        self.end_slider.blockSignals(True)

        self.start_slider.setValue(int(start_time * 100))
        self.end_slider.setValue(int(end_time * 100))

        self.start_slider.blockSignals(False)
        self.end_slider.blockSignals(False)

        self.update_current_segment()
        self.update_duration_display()
        self.validate_current_segment()

    def on_start_slider_changed(self, value):
        """Appelé lors du déplacement du slider de début"""
        start_time = value / 100.0
        self.start_time_spin.blockSignals(True)
        self.start_time_spin.set_time_value(start_time)
        self.start_time_spin.blockSignals(False)
        self.on_timing_changed()

    def on_end_slider_changed(self, value):
        """Appelé lors du déplacement du slider de fin"""
        end_time = value / 100.0
        self.end_time_spin.blockSignals(True)
        self.end_time_spin.set_time_value(end_time)
        self.end_time_spin.blockSignals(False)
        self.on_timing_changed()

    def adjust_timing(self, delta: float):
        """Ajuste les timestamps de début et fin"""
        start_time = self.start_time_spin.get_time_value() + delta
        end_time = self.end_time_spin.get_time_value() + delta

        # S'assurer que les valeurs sont dans les limites
        start_time = max(0, start_time)
        if self.video_duration:
            end_time = min(self.video_duration, end_time)

        if start_time < end_time:
            self.start_time_spin.set_time_value(start_time)
            self.end_time_spin.set_time_value(end_time)

    def update_current_segment(self):
        """Met à jour le segment actuel avec les valeurs de l'interface"""
        self.current_segment['title'] = self.title_edit.text().strip()
        self.current_segment['summary'] = self.summary_edit.toPlainText().strip()

        # Mots-clés
        keywords_text = self.keywords_edit.text().strip()
        if keywords_text:
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            self.current_segment['keywords'] = keywords
        else:
            self.current_segment['keywords'] = []

        self.current_segment['importance'] = self.importance_spin.value()

        # Timestamps
        start_time = self.start_time_spin.get_time_value()
        end_time = self.end_time_spin.get_time_value()

        self.current_segment['start_seconds'] = start_time
        self.current_segment['end_seconds'] = end_time
        self.current_segment['start_time'] = start_time
        self.current_segment['end_time'] = end_time

        # Avancé
        self.current_segment['confidence'] = self.confidence_spin.value()
        self.current_segment['theme_based'] = self.theme_based_check.isChecked()

        # Recalculer la durée
        duration = end_time - start_time
        self.current_segment['duration'] = self.format_duration(duration)

    def update_duration_display(self):
        """Met à jour l'affichage de la durée"""
        start_time = self.start_time_spin.get_time_value()
        end_time = self.end_time_spin.get_time_value()
        duration = end_time - start_time

        if duration > 0:
            duration_text = self.format_duration(duration)
            self.duration_label.setText(duration_text)
            self.duration_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.duration_label.setText("Durée invalide")
            self.duration_label.setStyleSheet("font-weight: bold; color: red;")

    def update_tech_info(self):
        """Met à jour les informations techniques"""
        info_parts = []

        if 'chunk_source' in self.current_segment:
            info_parts.append(f"Source: Chunk {self.current_segment['chunk_source']}")

        if self.video_duration:
            start_pct = (self.start_time_spin.get_time_value() / self.video_duration) * 100
            end_pct = (self.end_time_spin.get_time_value() / self.video_duration) * 100
            info_parts.append(f"Position: {start_pct:.1f}% - {end_pct:.1f}%")

        self.tech_info_label.setText(" | ".join(info_parts))

    def validate_current_segment(self):
        """Valide le segment actuel et affiche les erreurs"""
        is_valid, errors = SegmentValidator.validate_segment(self.current_segment, self.video_duration)

        if is_valid:
            self.validation_label.setText("✓ Segment valide")
            self.validation_label.setStyleSheet("color: green; font-weight: bold;")
            self.apply_btn.setEnabled(True)
        else:
            error_text = "⚠ Erreurs:\n" + "\n".join(f"• {error}" for error in errors)
            self.validation_label.setText(error_text)
            self.validation_label.setStyleSheet("color: red;")
            self.apply_btn.setEnabled(False)

    def preview_segment(self):
        """Prévisualise le segment (à implémenter)"""
        QMessageBox.information(
            self,
            "Prévisualisation",
            "Fonctionnalité de prévisualisation à venir.\n"
            f"Segment: {self.current_segment.get('title', 'Sans titre')}\n"
            f"Durée: {self.current_segment.get('duration', 'N/A')}"
        )

    def reset_to_original(self):
        """Remet les valeurs d'origine"""
        self.current_segment = self.original_segment.copy()
        self.load_segment_data()

    def apply_changes(self):
        """Applique les modifications"""
        self.update_current_segment()

        is_valid, errors = SegmentValidator.validate_segment(self.current_segment, self.video_duration)

        if not is_valid:
            error_msg = "Impossible d'appliquer les modifications:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Validation échouée", error_msg)
            return

        self.segment_updated.emit(self.current_segment)
        self.accept()

    def format_duration(self, seconds: float) -> str:
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


class SegmentListManager:
    """Gestionnaire pour la liste des segments avec opérations d'édition"""

    def __init__(self, list_widget: QListWidget):
        self.list_widget = list_widget
        self.segments = []
        self.video_duration = None

    def set_segments(self, segments: List[Dict[str, Any]], video_duration: float = None):
        """Définit la liste des segments"""
        self.segments = segments.copy()
        self.video_duration = video_duration
        self.refresh_display()

    def refresh_display(self):
        """Actualise l'affichage de la liste"""
        self.list_widget.clear()

        for i, segment in enumerate(self.segments):
            title = segment.get('title', f'Segment {i+1}')
            duration = segment.get('duration', 'N/A')
            importance = segment.get('importance', 3)

            item_text = f"{i+1:02d}. {title} ({duration})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, {'index': i, 'segment': segment})

            # Couleur selon l'importance
            if importance >= 4:
                item.setBackground(Qt.lightGray)  # Haute importance
            elif importance <= 2:
                item.setBackground(Qt.yellow)    # Basse importance

            self.list_widget.addItem(item)

    def get_selected_segment(self) -> Optional[tuple[int, Dict[str, Any]]]:
        """Récupère le segment sélectionné"""
        current_item = self.list_widget.currentItem()
        if current_item:
            data = current_item.data(Qt.UserRole)
            return data['index'], data['segment']
        return None

    def edit_segment(self, index: int) -> bool:
        """Ouvre l'éditeur pour un segment"""
        if 0 <= index < len(self.segments):
            segment = self.segments[index]

            dialog = SegmentEditDialog(segment, self.video_duration)
            dialog.segment_updated.connect(lambda updated: self.update_segment(index, updated))

            return dialog.exec_() == QDialog.Accepted

        return False

    def update_segment(self, index: int, updated_segment: Dict[str, Any]):
        """Met à jour un segment"""
        if 0 <= index < len(self.segments):
            self.segments[index] = updated_segment
            self.refresh_display()
            logger.info(f"Segment {index+1} mis à jour: {updated_segment.get('title', 'Sans titre')}")

    def delete_segment(self, index: int) -> bool:
        """Supprime un segment"""
        if 0 <= index < len(self.segments):
            segment = self.segments[index]
            reply = QMessageBox.question(
                self.list_widget,
                "Supprimer le segment",
                f"Êtes-vous sûr de vouloir supprimer le segment '{segment.get('title', 'Sans titre')}' ?"
            )

            if reply == QMessageBox.Yes:
                del self.segments[index]
                self.refresh_display()
                logger.info(f"Segment {index+1} supprimé")
                return True

        return False

    def move_segment(self, from_index: int, to_index: int) -> bool:
        """Déplace un segment dans la liste"""
        if (0 <= from_index < len(self.segments) and
            0 <= to_index < len(self.segments) and
            from_index != to_index):

            segment = self.segments.pop(from_index)
            self.segments.insert(to_index, segment)
            self.refresh_display()

            logger.info(f"Segment déplacé de {from_index+1} vers {to_index+1}")
            return True

        return False

    def get_all_segments(self) -> List[Dict[str, Any]]:
        """Récupère tous les segments"""
        return self.segments.copy()