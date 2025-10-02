# -*- coding: utf-8 -*-

import logging
import json
import re
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import ollama

from config import Config

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Analyseur IA utilisant Ollama pour identifier les thèmes et points de découpe"""

    def __init__(self):
        self.client = ollama.Client()
        self.model_name = Config.OLLAMA_MODEL
        self.max_tokens = Config.MAX_TOKENS_PER_ANALYSIS

        logger.info(f"Analyseur IA configuré avec le modèle: {self.model_name}")

    def check_model_availability(self) -> bool:
        """Vérifie si le modèle Ollama est disponible"""
        try:
            models_response = self.client.list()
            # L'API Ollama retourne un objet ListResponse avec un attribut models
            available_models = [model.model for model in models_response.models]

            if self.model_name in available_models:
                logger.info(f"Modèle {self.model_name} disponible")
                return True
            else:
                logger.warning(f"Modèle {self.model_name} non trouvé. Modèles disponibles: {available_models}")
                return False

        except Exception as e:
            logger.error(f"Erreur lors de la vérification du modèle: {e}")
            return False

    def ensure_model_loaded(self) -> bool:
        """S'assure que le modèle est chargé et disponible"""
        try:
            if not self.check_model_availability():
                logger.info(f"Téléchargement du modèle {self.model_name}...")

                # Pull du modèle si non disponible
                self.client.pull(self.model_name)

                # Vérifier à nouveau
                return self.check_model_availability()

            return True

        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            return False

    def split_transcript_into_chunks(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Divise une transcription longue en chunks analysables
        Maintient la cohérence des segments
        """
        full_text = transcript['text']
        segments = transcript['segments']

        if len(full_text.split()) <= self.max_tokens:
            return [{
                'text': full_text,
                'segments': segments,
                'start_time': segments[0]['start'] if segments else 0,
                'end_time': segments[-1]['end'] if segments else 0,
                'chunk_index': 0
            }]

        logger.info("Division de la transcription en chunks pour analyse")

        chunks = []
        current_chunk = {
            'text_parts': [],
            'segments': [],
            'word_count': 0
        }

        for segment in segments:
            segment_words = len(segment['text'].split())

            # Si ajouter ce segment dépasse la limite
            if current_chunk['word_count'] + segment_words > self.max_tokens:
                if current_chunk['segments']:  # Sauvegarder le chunk actuel s'il n'est pas vide
                    chunk_text = ' '.join(current_chunk['text_parts'])
                    chunks.append({
                        'text': chunk_text,
                        'segments': current_chunk['segments'],
                        'start_time': current_chunk['segments'][0]['start'],
                        'end_time': current_chunk['segments'][-1]['end'],
                        'chunk_index': len(chunks)
                    })

                # Démarrer un nouveau chunk
                current_chunk = {
                    'text_parts': [segment['text']],
                    'segments': [segment],
                    'word_count': segment_words
                }
            else:
                # Ajouter au chunk actuel
                current_chunk['text_parts'].append(segment['text'])
                current_chunk['segments'].append(segment)
                current_chunk['word_count'] += segment_words

        # Ajouter le dernier chunk
        if current_chunk['segments']:
            chunk_text = ' '.join(current_chunk['text_parts'])
            chunks.append({
                'text': chunk_text,
                'segments': current_chunk['segments'],
                'start_time': current_chunk['segments'][0]['start'],
                'end_time': current_chunk['segments'][-1]['end'],
                'chunk_index': len(chunks)
            })

        logger.info(f"Transcription divisée en {len(chunks)} chunks")
        return chunks

    def generate_analysis_prompt(self, text: str, chunk_info: str = "") -> str:
        """Génère le prompt d'analyse pour le modèle IA"""
        prompt = f"""Tu es un expert en analyse de contenu vidéo d'interviews. Analyse cette transcription d'interview {chunk_info} et identifie:

1. THÈMES PRINCIPAUX: Les différents sujets abordés
2. POINTS DE DÉCOUPE: Moments naturels pour diviser la vidéo (transitions entre sujets, pauses)
3. LIEUX MENTIONNÉS: Villes, villages, lieux géographiques
4. MOTS-CLÉS: Concepts importants, noms propres

TRANSCRIPTION À ANALYSER:
{text}

RÉPONDS UNIQUEMENT EN JSON avec cette structure exacte:
{{
  "themes": [
    {{
      "title": "Titre du thème",
      "description": "Description courte",
      "start_approximate": 123.45,
      "end_approximate": 234.56,
      "keywords": ["mot1", "mot2"],
      "importance": 1-5
    }}
  ],
  "cut_points": [
    {{
      "timestamp": 123.45,
      "reason": "Transition vers nouveau sujet",
      "confidence": 1-5
    }}
  ],
  "locations": ["Paris", "Marseille"],
  "global_keywords": ["métier", "tradition", "famille"]
}}

IMPORTANT:
- Utilise les timestamps réels de la transcription
- Privilégie les transitions naturelles
- Évite de couper au milieu de phrases importantes
- Les thèmes doivent être cohérents et distincts"""

        return prompt

    def query_model(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Interroge le modèle Ollama avec gestion des erreurs"""
        for attempt in range(max_retries):
            try:
                logger.debug(f"Requête au modèle (tentative {attempt + 1})")

                response = self.client.chat(
                    model=self.model_name,
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }],
                    options={
                        'temperature': 0.3,  # Moins de créativité, plus de précision
                        'top_p': 0.9,
                        'num_predict': 1000  # Limite de tokens de réponse
                    }
                )

                return response['message']['content']

            except Exception as e:
                logger.warning(f"Tentative {attempt + 1} échouée: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Toutes les tentatives ont échoué")
                    return None

                time.sleep(2 ** attempt)  # Backoff exponentiel

        return None

    def parse_ai_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse la réponse JSON du modèle IA"""
        try:
            # Nettoyer la réponse (enlever markdown, commentaires, etc.)
            response = response.strip()

            # Chercher le JSON dans la réponse
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Essayer de parser directement
                return json.loads(response)

        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {e}")
            logger.debug(f"Réponse reçue: {response[:500]}...")
            return None
        except Exception as e:
            logger.error(f"Erreur lors du parsing: {e}")
            return None

    def merge_chunk_analyses(self, chunk_analyses: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fusionne les analyses de plusieurs chunks en une analyse globale cohérente"""
        logger.info(f"Fusion de {len(chunk_analyses)} analyses de chunks")

        merged_analysis = {
            'themes': [],
            'cut_points': [],
            'locations': set(),
            'global_keywords': set()
        }

        for i, (analysis, chunk) in enumerate(zip(chunk_analyses, chunks)):
            if not analysis:
                continue

            chunk_offset = chunk['start_time']

            # Fusion des thèmes
            for theme in analysis.get('themes', []):
                merged_theme = theme.copy()
                # Ajuster les timestamps avec l'offset du chunk
                merged_theme['start_approximate'] += chunk_offset
                merged_theme['end_approximate'] += chunk_offset
                merged_theme['chunk_source'] = i
                merged_analysis['themes'].append(merged_theme)

            # Fusion des points de coupe
            for cut_point in analysis.get('cut_points', []):
                merged_cut = cut_point.copy()
                merged_cut['timestamp'] += chunk_offset
                merged_cut['chunk_source'] = i
                merged_analysis['cut_points'].append(merged_cut)

            # Fusion des lieux et mots-clés
            merged_analysis['locations'].update(analysis.get('locations', []))
            merged_analysis['global_keywords'].update(analysis.get('global_keywords', []))

        # Convertir les sets en listes
        merged_analysis['locations'] = list(merged_analysis['locations'])
        merged_analysis['global_keywords'] = list(merged_analysis['global_keywords'])

        # Trier et dédupliquer les points de coupe
        merged_analysis['cut_points'] = sorted(
            merged_analysis['cut_points'],
            key=lambda x: x['timestamp']
        )

        # Nettoyer les thèmes en double ou qui se chevauchent
        merged_analysis['themes'] = self.clean_overlapping_themes(merged_analysis['themes'])

        return merged_analysis

    def clean_overlapping_themes(self, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Nettoie les thèmes qui se chevauchent ou sont redondants"""
        if not themes:
            return themes

        # Trier par timestamp de début
        sorted_themes = sorted(themes, key=lambda x: x.get('start_approximate', 0))

        cleaned_themes = []
        for theme in sorted_themes:
            # Vérifier si ce thème chevauche significativement avec le précédent
            if cleaned_themes:
                last_theme = cleaned_themes[-1]
                overlap = self.calculate_theme_overlap(last_theme, theme)

                if overlap > 0.5:  # Plus de 50% de chevauchement
                    # Fusionner les thèmes
                    merged_theme = self.merge_themes(last_theme, theme)
                    cleaned_themes[-1] = merged_theme
                    continue

            cleaned_themes.append(theme)

        logger.debug(f"Thèmes nettoyés: {len(themes)} -> {len(cleaned_themes)}")
        return cleaned_themes

    def calculate_theme_overlap(self, theme1: Dict[str, Any], theme2: Dict[str, Any]) -> float:
        """Calcule le pourcentage de chevauchement entre deux thèmes"""
        start1, end1 = theme1.get('start_approximate', 0), theme1.get('end_approximate', 0)
        start2, end2 = theme2.get('start_approximate', 0), theme2.get('end_approximate', 0)

        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_end <= overlap_start:
            return 0.0

        overlap_duration = overlap_end - overlap_start
        theme1_duration = end1 - start1
        theme2_duration = end2 - start2

        if theme1_duration == 0 or theme2_duration == 0:
            return 0.0

        # Pourcentage par rapport au thème le plus court
        min_duration = min(theme1_duration, theme2_duration)
        return overlap_duration / min_duration

    def merge_themes(self, theme1: Dict[str, Any], theme2: Dict[str, Any]) -> Dict[str, Any]:
        """Fusionne deux thèmes qui se chevauchent"""
        merged = {
            'title': f"{theme1.get('title', '')} / {theme2.get('title', '')}",
            'description': f"{theme1.get('description', '')} - {theme2.get('description', '')}",
            'start_approximate': min(theme1.get('start_approximate', 0), theme2.get('start_approximate', 0)),
            'end_approximate': max(theme1.get('end_approximate', 0), theme2.get('end_approximate', 0)),
            'keywords': list(set(theme1.get('keywords', []) + theme2.get('keywords', []))),
            'importance': max(theme1.get('importance', 1), theme2.get('importance', 1))
        }

        return merged

    def create_video_segments(self, analysis: Dict[str, Any], transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crée les segments vidéo finaux basés sur l'analyse IA"""
        logger.info("Création des segments vidéo à partir de l'analyse")

        segments = []

        # Utiliser les thèmes comme base pour les segments
        themes = sorted(analysis.get('themes', []), key=lambda x: x.get('start_approximate', 0))

        for i, theme in enumerate(themes):
            start_time = theme.get('start_approximate', 0)
            end_time = theme.get('end_approximate', 0)

            # Ajuster les points de début/fin avec les points de coupe suggérés
            start_time = self.find_best_cut_point(start_time, analysis.get('cut_points', []), 'start')
            end_time = self.find_best_cut_point(end_time, analysis.get('cut_points', []), 'end')

            # Éviter les segments trop courts (moins de 30 secondes)
            if end_time - start_time < 30:
                if i < len(themes) - 1:  # Pas le dernier segment
                    continue  # Skip ce segment trop court

            # Créer le segment
            segment = {
                'title': self.clean_title(theme.get('title', f'Extrait {i+1}')),
                'start_time': start_time,
                'end_time': end_time,
                'start_seconds': start_time,
                'end_seconds': end_time,
                'duration': self.format_duration(end_time - start_time),
                'summary': theme.get('description', ''),
                'keywords': theme.get('keywords', []),
                'importance': theme.get('importance', 3),
                'theme_based': True
            }

            segments.append(segment)

        # Si aucun thème n'a été détecté, créer des segments basés sur les points de coupe
        if not segments:
            segments = self.create_segments_from_cut_points(analysis.get('cut_points', []), transcript)

        # Si toujours aucun segment, diviser en parties égales
        if not segments:
            segments = self.create_fallback_segments(transcript)

        logger.info(f"{len(segments)} segments vidéo créés")
        return segments

    def find_best_cut_point(self, target_time: float, cut_points: List[Dict[str, Any]], point_type: str) -> float:
        """Trouve le meilleur point de coupe proche du temps cible"""
        if not cut_points:
            return target_time

        # Chercher le point de coupe le plus proche
        best_point = min(
            cut_points,
            key=lambda cp: abs(cp.get('timestamp', 0) - target_time)
        )

        best_time = best_point.get('timestamp', target_time)
        distance = abs(best_time - target_time)

        # N'utiliser le point de coupe que s'il est proche (moins de 30 secondes)
        if distance <= 30 and best_point.get('confidence', 1) >= 3:
            return best_time

        return target_time

    def create_segments_from_cut_points(self, cut_points: List[Dict[str, Any]], transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crée des segments basés uniquement sur les points de coupe"""
        if not cut_points:
            return []

        segments = []
        sorted_cuts = sorted(cut_points, key=lambda x: x.get('timestamp', 0))

        total_duration = transcript.get('metadata', {}).get('total_duration', 0)
        current_start = 0

        for i, cut_point in enumerate(sorted_cuts):
            end_time = cut_point.get('timestamp', 0)

            if end_time - current_start > 30:  # Segment assez long
                segment = {
                    'title': f'Segment {len(segments) + 1}',
                    'start_time': current_start,
                    'end_time': end_time,
                    'start_seconds': current_start,
                    'end_seconds': end_time,
                    'duration': self.format_duration(end_time - current_start),
                    'summary': f'Segment créé automatiquement ({cut_point.get("reason", "point de coupe détecté")})',
                    'keywords': [],
                    'importance': 3,
                    'theme_based': False
                }
                segments.append(segment)
                current_start = end_time

        # Ajouter le dernier segment si nécessaire
        if current_start < total_duration - 30:
            segment = {
                'title': f'Segment {len(segments) + 1}',
                'start_time': current_start,
                'end_time': total_duration,
                'start_seconds': current_start,
                'end_seconds': total_duration,
                'duration': self.format_duration(total_duration - current_start),
                'summary': 'Segment final',
                'keywords': [],
                'importance': 3,
                'theme_based': False
            }
            segments.append(segment)

        return segments

    def create_fallback_segments(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crée des segments de base si l'analyse IA échoue"""
        logger.warning("Création de segments de secours")

        total_duration = transcript.get('metadata', {}).get('total_duration', 600)
        segment_duration = min(300, total_duration / 3)  # Max 5 minutes par segment

        segments = []
        current_start = 0

        while current_start < total_duration:
            end_time = min(current_start + segment_duration, total_duration)

            segment = {
                'title': f'Extrait {len(segments) + 1}',
                'start_time': current_start,
                'end_time': end_time,
                'start_seconds': current_start,
                'end_seconds': end_time,
                'duration': self.format_duration(end_time - current_start),
                'summary': 'Segment créé automatiquement',
                'keywords': [],
                'importance': 3,
                'theme_based': False
            }

            segments.append(segment)
            current_start = end_time

        return segments

    def clean_title(self, title: str) -> str:
        """Nettoie et améliore les titres de segments"""
        if not title:
            return "Extrait"

        # Supprimer les caractères problématiques
        cleaned = re.sub(r'[^\w\s\-àéèêëîïôöùûüÿç]', '', title)

        # Limiter la longueur
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "..."

        # Capitaliser
        return cleaned.strip().title() if cleaned.strip() else "Extrait"

    def format_duration(self, seconds: float) -> str:
        """Formate une durée en secondes vers un format lisible"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m{secs:02d}s"

    def analyze_transcript(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyse complète d'une transcription
        Retourne une liste de segments vidéo recommandés
        """
        logger.info("Début de l'analyse IA de la transcription")
        start_time = time.time()

        try:
            # Vérifier et charger le modèle
            if not self.ensure_model_loaded():
                raise RuntimeError("Modèle IA non disponible")

            # Diviser la transcription en chunks si nécessaire
            chunks = self.split_transcript_into_chunks(transcript)

            # Analyser chaque chunk
            chunk_analyses = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Analyse du chunk {i+1}/{len(chunks)}")

                chunk_info = f"(partie {i+1}/{len(chunks)})" if len(chunks) > 1 else ""
                prompt = self.generate_analysis_prompt(chunk['text'], chunk_info)

                response = self.query_model(prompt)
                if response:
                    analysis = self.parse_ai_response(response)
                    chunk_analyses.append(analysis)
                else:
                    logger.warning(f"Échec de l'analyse du chunk {i+1}")
                    chunk_analyses.append(None)

            # Fusionner les analyses
            if any(analysis for analysis in chunk_analyses):
                merged_analysis = self.merge_chunk_analyses(chunk_analyses, chunks)
            else:
                logger.error("Toutes les analyses ont échoué")
                merged_analysis = {'themes': [], 'cut_points': []}

            # Créer les segments finaux
            segments = self.create_video_segments(merged_analysis, transcript)

            analysis_time = time.time() - start_time
            logger.info(f"Analyse terminée en {analysis_time:.2f}s - {len(segments)} segments créés")

            return segments

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            # Retourner des segments de base en cas d'erreur
            return self.create_fallback_segments(transcript)