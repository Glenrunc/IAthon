"""Logique métier pour le module Service Client."""

from __future__ import annotations

from typing import Any

from core.helpers import appeler_llm_texte


def analyser_avis_client(avis: str, nom_entreprise: str, nom_gerant: str) -> dict[str, Any]:
    """
    Analyse un avis client et génère une réponse professionnelle.

    Args:
        avis: Avis client à analyser.
        nom_entreprise: Nom de l'entreprise.
        nom_gerant: Nom du gérant.

    Returns:
        Dictionnaire contenant le sentiment et le brouillon de réponse.
    """
    prompt = f"""Voici un avis client laissé pour l'entreprise {nom_entreprise} :
"{avis}"

Fais deux choses :
1. SENTIMENT : Indique le sentiment général (Positif, Neutre, ou Négatif). Réponds juste avec le mot, suivi d'un emoji.
2. REPONSE : Rédige un brouillon de réponse polie, professionnelle et empathique.
La réponse DOIT être signée par {nom_gerant}, de la part de l'entreprise {nom_entreprise}.

Sépare les deux parties avec "---"""

    reponse = appeler_llm_texte(prompt)

    try:
        sentiment, brouillon = reponse.split("---")
        sentiment = sentiment.strip()
        brouillon = brouillon.strip()

        return {
            'sentiment': sentiment,
            'brouillon': brouillon,
            'avis_original': avis
        }
    except ValueError:
        return {
            'sentiment': 'Inconnu',
            'brouillon': reponse,
            'avis_original': avis
        }
