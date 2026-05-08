"""Logique métier pour le module RH & Recrutement."""

from __future__ import annotations

from typing import Any

from core.helpers import appeler_llm_texte
from core.pdf_reader import read_text


def analyser_candidature(description_poste: str, cv_texte: str) -> str:
    """
    Analyse la compatibilité d'un candidat avec un poste.

    Args:
        description_poste: Description du poste à pourvoir.
        cv_texte: Texte extrait du CV du candidat.

    Returns:
        Analyse structurée de la candidature (score, points forts, lacunes, questions).
    """
    prompt = f"""Tu es un expert en recrutement (RH).
Voici la description d'un poste :
---
{description_poste}
---
Et voici le contenu du CV d'un candidat :
---
{cv_texte}
---
Réalise une analyse structurée :
1. SCORE : Donne un score d'adéquation de 0 à 100%.
2. POINTS FORTS : 3 points forts du candidat pour ce poste.
3. LACUNES : Compétences ou expériences manquantes.
4. QUESTIONS : Propose 3 questions d'entretien spécifiques pour creuser les zones d'ombre.

Réponds de manière concise et professionnelle."""

    return appeler_llm_texte(prompt)
