"""Logique métier pour le module Marketing."""

from __future__ import annotations

from typing import Any

from core.helpers import appeler_llm_texte


def generer_contenu_marketing(
    nom_produit: str,
    public_cible: str,
    caracteristiques: str,
    nom_entreprise: str
) -> dict[str, Any]:
    """
    Génère du contenu marketing pour un produit.

    Args:
        nom_produit: Nom du produit.
        public_cible: Public cible du produit.
        caracteristiques: Caractéristiques du produit.
        nom_entreprise: Nom de l'entreprise.

    Returns:
        Dictionnaire contenant la fiche produit et le post social.
    """
    prompt = f"""Tu es un copywriter expert en e-commerce pour l'entreprise {nom_entreprise}.
À partir des informations suivantes :
- Produit : {nom_produit}
- Cible : {public_cible if public_cible else "Grand public"}
- Caractéristiques : {caracteristiques}

Rédige :
1. [FICHE] Une fiche produit attractive (3-4 phrases courtes) optimisée pour être vendue par {nom_entreprise}.
2. [SOCIAL] Un post pour Instagram dynamique, rédigé au nom de l'entreprise {nom_entreprise}, incluant des emojis pertinents et 3 à 5 hashtags adaptés."""

    reponse = appeler_llm_texte(prompt)

    resultat = {}

    if "[SOCIAL]" in reponse:
        fiche, social = reponse.split("[SOCIAL]")
        resultat['fiche'] = fiche.replace("[FICHE]", "").strip()
        resultat['social'] = social.strip()
    else:
        resultat['fiche'] = reponse
        resultat['social'] = None

    resultat['nom_produit'] = nom_produit

    return resultat
