"""Utilitaires communs pour l'application."""

from __future__ import annotations

import json
import os
import re
import socket
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

_CLIENT: Any = None
_MODELE_DISPONIBLE: str | None = None
_RATE_LIMIT_RE = re.compile(r"quota|rate.?limit|429", re.IGNORECASE)


def configurer_api() -> bool:
    """Initialise le client Google GenAI."""
    global _CLIENT
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return False
    try:
        from google import genai

        _CLIENT = genai.Client(api_key=api_key)
        return True
    except Exception:
        return False


def obtenir_modele() -> str:
    """Détecte dynamiquement le meilleur modèle disponible pour la clé API."""
    global _MODELE_DISPONIBLE
    if _MODELE_DISPONIBLE:
        return _MODELE_DISPONIBLE

    try:
        modeles_obj = _CLIENT.models.list()
        modeles = [m.name for m in modeles_obj]

        preferences = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash']

        for pref in preferences:
            if pref in modeles or f"models/{pref}" in modeles:
                _MODELE_DISPONIBLE = pref
                return _MODELE_DISPONIBLE

        if modeles:
            _MODELE_DISPONIBLE = modeles[0].replace('models/', '')
            return _MODELE_DISPONIBLE
    except Exception:
        pass

    return 'gemini-1.5-flash'


def _classer_erreur(e: Exception) -> Exception:
    """Classifie une exception en fonction de son type."""
    if isinstance(e, (socket.timeout, TimeoutError)):
        return Exception(f"Network timeout: {e}")

    try:
        import requests
        if isinstance(e, requests.exceptions.Timeout):
            return Exception(f"Request timeout: {e}")
    except ImportError:
        pass

    msg = str(e)
    if _RATE_LIMIT_RE.search(msg):
        return Exception(f"Rate limit exceeded: {e}")

    return e


def appeler_llm_texte(prompt: str) -> str:
    """Appelle le LLM pour du texte simple avec gestion avancée des quotas (429)."""
    global _MODELE_DISPONIBLE
    for tentative in range(3):
        nom_modele = obtenir_modele()
        try:
            response = _CLIENT.models.generate_content(
                model=nom_modele,
                contents=prompt
            )
            return response.text
        except Exception as e:
            erreur = _classer_erreur(e)
            if "Rate limit" in str(erreur) or "Network timeout" in str(erreur) or "Request timeout" in str(erreur):
                if tentative < 2:
                    if "Rate limit" in str(erreur):
                        _MODELE_DISPONIBLE = None
                        time.sleep(20)
                    else:
                        time.sleep(2)
                    continue
            return f"Erreur lors de l'appel texte ({nom_modele}) : {str(erreur)}"


def appeler_llm_vision(prompt: str, image_pil: Any) -> str:
    """Appelle le LLM pour l'analyse d'images avec bascule de modèle en cas de 429."""
    global _MODELE_DISPONIBLE
    for tentative in range(3):
        nom_modele = obtenir_modele()
        try:
            response = _CLIENT.models.generate_content(
                model=nom_modele,
                contents=[image_pil, prompt]
            )
            return response.text
        except Exception as e:
            erreur = _classer_erreur(e)
            if "Rate limit" in str(erreur) or "Network timeout" in str(erreur) or "Request timeout" in str(erreur):
                if tentative < 2:
                    if "Rate limit" in str(erreur):
                        _MODELE_DISPONIBLE = None
                        time.sleep(20)
                    else:
                        time.sleep(2)
                    continue
            return f"Erreur lors de l'appel vision ({nom_modele}) : {str(erreur)}"


def appeler_llm_multimodal(prompt: str, mime_type: str, file_bytes: bytes) -> str:
    """Appelle le LLM pour des fichiers complexes avec gestion de quota."""
    global _MODELE_DISPONIBLE
    for tentative in range(3):
        nom_modele = obtenir_modele()
        try:
            response = _CLIENT.models.generate_content(
                model=nom_modele,
                contents=[
                    {"mime_type": mime_type, "data": file_bytes},
                    prompt
                ]
            )
            return response.text
        except Exception as e:
            erreur = _classer_erreur(e)
            if "Rate limit" in str(erreur) or "Network timeout" in str(erreur) or "Request timeout" in str(erreur):
                if tentative < 2:
                    if "Rate limit" in str(erreur):
                        _MODELE_DISPONIBLE = None
                        time.sleep(20)
                    else:
                        time.sleep(2)
                    continue
            return f"Erreur lors de l'appel multimodal ({nom_modele}) : {str(erreur)}"


class QuotaExhaustedError(Exception):
    """Exception levée quand le quota API est épuisé."""
    pass


def appeler_llm_json(prompt: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Appelle le LLM avec un retour JSON natif via Structured Outputs.

    Args:
        prompt: Le prompt à envoyer au LLM.
        schema: Optionnel. Un schéma JSON pour contraindre la sortie.

    Returns:
        Un dictionnaire Python parsé depuis le JSON retourné par le LLM.

    Raises:
        QuotaExhaustedError: Quand le quota API est épuisé (erreur 429).
        Exception: Autres erreurs lors de l'appel au LLM.
    """
    global _MODELE_DISPONIBLE

    from google.genai import types

    config_params = {"response_mime_type": "application/json"}

    if schema is not None:
        config_params["response_schema"] = schema

    config = types.GenerateContentConfig(**config_params)

    for tentative in range(3):
        nom_modele = obtenir_modele()
        try:
            response = _CLIENT.models.generate_content(
                model=nom_modele,
                contents=prompt,
                config=config
            )
            if response.text:
                return json.loads(response.text)
            return {}
        except Exception as e:
            erreur = _classer_erreur(e)
            if "Rate limit" in str(erreur):
                if tentative < 2:
                    _MODELE_DISPONIBLE = None
                    raise QuotaExhaustedError(
                        "Le quota de l'IA est temporairement épuisé. "
                        "Veuillez réessayer dans quelques secondes."
                    )
            raise Exception(f"Erreur lors de l'appel JSON ({nom_modele}) : {str(erreur)}")


def appeler_llm_vision_json(prompt: str, image_pil: Any, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Appelle le LLM pour l'analyse d'images avec un retour JSON natif.

    Args:
        prompt: Le prompt à envoyer au LLM.
        image_pil: Image PIL à analyser.
        schema: Optionnel. Un schéma JSON pour contraindre la sortie.

    Returns:
        Un dictionnaire Python parsé depuis le JSON retourné par le LLM.

    Raises:
        QuotaExhaustedError: Quand le quota API est épuisé (erreur 429).
        Exception: Autres erreurs lors de l'appel au LLM.
    """
    global _MODELE_DISPONIBLE

    from google.genai import types

    config_params = {"response_mime_type": "application/json"}

    if schema is not None:
        config_params["response_schema"] = schema

    config = types.GenerateContentConfig(**config_params)

    for tentative in range(3):
        nom_modele = obtenir_modele()
        try:
            response = _CLIENT.models.generate_content(
                model=nom_modele,
                contents=[image_pil, prompt],
                config=config
            )
            if response.text:
                return json.loads(response.text)
            return {}
        except Exception as e:
            erreur = _classer_erreur(e)
            if "Rate limit" in str(erreur):
                if tentative < 2:
                    _MODELE_DISPONIBLE = None
                    raise QuotaExhaustedError(
                        "Le quota de l'IA est temporairement épuisé. "
                        "Veuillez réessayer dans quelques secondes."
                    )
            raise Exception(f"Erreur lors de l'appel vision JSON ({nom_modele}) : {str(erreur)}")


def appeler_llm_vision_json_bytes(prompt: str, file_bytes: bytes, mime: str, model: str = "gemini-1.5-flash") -> str:
    """
    Appelle le LLM pour l'analyse de fichiers avec un retour JSON natif.

    Args:
        prompt: Le prompt à envoyer au LLM.
        file_bytes: Bytes du fichier à analyser.
        mime: Type MIME du fichier.
        model: Modèle à utiliser.

    Returns:
        Texte JSON retourné par le LLM.

    Raises:
        Exception: Erreurs lors de l'appel au LLM.
    """
    global _MODELE_DISPONIBLE

    for tentative in range(3):
        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )

            response = _CLIENT.models.generate_content(
                model=model,
                contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type=mime)],
                config=config
            )
            return response.text
        except Exception as e:
            erreur = _classer_erreur(e)
            if "Rate limit" in str(erreur) or "Network timeout" in str(erreur) or "Request timeout" in str(erreur):
                if tentative < 2:
                    if "Rate limit" in str(erreur):
                        _MODELE_DISPONIBLE = None
                        time.sleep(20)
                    else:
                        time.sleep(2)
                    continue
            raise Exception(f"Erreur lors de l'appel vision JSON bytes ({model}) : {str(erreur)}")
