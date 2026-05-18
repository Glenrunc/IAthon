"""Logique métier pour le module Configuration."""

from __future__ import annotations

import json
import os
from typing import Any
from PIL import Image


def charger_configuration() -> dict[str, Any]:
    """
    Charge les paramètres de l'entreprise depuis le fichier local config.json.

    Returns:
        Dictionnaire contenant la configuration de l'entreprise.
    """
    config_file = "config.json"

    config = {
        'entreprise_nom': "Ma PME",
        'entreprise_gerant': "Le Gérant",
        'logo_path': None
    }

    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                config['entreprise_nom'] = config_data.get("entreprise_nom", "Ma PME")
                config['entreprise_gerant'] = config_data.get("entreprise_gerant", "Le Gérant")
                config['logo_path'] = config_data.get("logo_path")
        except Exception:
            pass

    return config


def sauvegarder_configuration(
    nom: str,
    gerant: str,
    logo_upload: Any | None = None
) -> dict[str, Any]:
    """
    Sauvegarde la configuration de l'entreprise.

    Args:
        nom: Nom de l'entreprise.
        gerant: Nom du gérant.
        logo_upload: Fichier logo à sauvegarder (optionnel).

    Returns:
        Dictionnaire contenant la configuration sauvegardée.
    """
    logo_path = None

    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                old_config = json.load(f)
                logo_path = old_config.get("logo_path")
        except Exception:
            pass

    if logo_upload is not None:
        try:
            if not os.path.exists("assets"):
                os.makedirs("assets")

            image = Image.open(logo_upload)
            logo_path = "assets/logo_entreprise.png"
            image.save(logo_path)
        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde de l'image sur le disque: {e}")

    config_data = {
        "entreprise_nom": nom,
        "entreprise_gerant": gerant,
        "logo_path": logo_path
    }

    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise Exception(f"Erreur lors de la sauvegarde du fichier JSON : {e}")

    return config_data


def charger_logo(logo_path: str | None) -> Image.Image | None:
    """
    Charge le logo de l'entreprise depuis le chemin spécifié.

    Args:
        logo_path: Chemin vers le fichier logo.

    Returns:
        Image PIL si le fichier existe, None sinon.
    """
    if logo_path and os.path.exists(logo_path):
        try:
            return Image.open(logo_path)
        except Exception:
            pass
    return None
