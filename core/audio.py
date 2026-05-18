"""Logique métier pour le module Audio."""

from __future__ import annotations

from typing import Any

from core.helpers import appeler_llm_multimodal


def generer_compte_rendu_reunion(audio_bytes: bytes, mime_type: str) -> str:
    """
    Génère un compte-rendu structuré à partir d'un enregistrement audio.

    Args:
        audio_bytes: Bytes du fichier audio.
        mime_type: Type MIME du fichier audio.

    Returns:
        Compte-rendu structuré de la réunion.
    """
    prompt = """Analyse cet enregistrement audio de réunion et rédige un compte-rendu structuré :
1. RÉSUMÉ : De quoi a-t-il été question (3 phrases max).
2. DÉCISIONS : Quelles décisions ont été prises ?
3. ACTIONS : Liste les tâches à accomplir (qui fait quoi si c'est précisé).
4. TON : Note l'ambiance générale de la réunion.

Sois très structuré et utilise des listes à puces."""

    return appeler_llm_multimodal(prompt, mime_type, audio_bytes)
