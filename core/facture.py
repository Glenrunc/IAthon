"""Logique métier pour la génération de factures PDF."""

from __future__ import annotations

import datetime
import os
import tempfile
from typing import Any

import pandas as pd
from fpdf import FPDF

from core.helpers import appeler_llm_texte


def generer_message_ia(df: pd.DataFrame, nom_client: str, nom_entreprise: str) -> str:
    """
    Génère un message de remerciement personnalisé avec l'IA basé sur les achats.

    Args:
        df: DataFrame contenant les articles achetés.
        nom_client: Nom du client.
        nom_entreprise: Nom de l'entreprise.

    Returns:
        Message de remerciement personnalisé.
    """
    if 'Description' in df.columns:
        articles = ", ".join(df['Description'].astype(str).tolist()[:3])
    else:
        articles = "plusieurs articles"

    prompt = f"""Tu es le gérant de l'entreprise '{nom_entreprise}'.
Ton client '{nom_client}' vient de t'acheter : {articles}.
Rédige un message de remerciement très court (max 200 caractères), chaleureux et professionnel.
Le message doit être humain et valorisant. Ne commence pas par "Cher client"."""
    return appeler_llm_texte(prompt)


def creer_pdf_facture(
    df: pd.DataFrame,
    client_nom: str,
    num_facture: str,
    date_facture: datetime.date,
    message_ia: str,
    taux_tva: float,
    nom_entreprise: str,
    gerant_nom: str,
    logo_path: str | None = None
) -> str:
    """
    Génère un PDF de facture avec un design professionnel et épuré.

    Args:
        df: DataFrame contenant les lignes de facturation.
        client_nom: Nom du client.
        num_facture: Numéro de facture.
        date_facture: Date de la facture.
        message_ia: Message personnalisé généré par l'IA.
        taux_tva: Taux de TVA en pourcentage.
        nom_entreprise: Nom de l'entreprise.
        gerant_nom: Nom du gérant.
        logo_path: Chemin vers le logo de l'entreprise (optionnel).

    Returns:
        Chemin vers le fichier PDF généré.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 20, 15)

    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=15, y=15, h=25)

    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, nom_entreprise.upper(), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Représenté par {gerant_nom}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(20)

    y_start = pdf.get_y()

    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(90, 5, "FACTURÉ À :", new_x="RIGHT")
    pdf.cell(0, 5, "DÉTAILS :", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 8, client_nom, new_x="RIGHT")
    pdf.cell(0, 8, f"Facture n° {num_facture}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 10)
    pdf.cell(90, 6, "", new_x="RIGHT")
    pdf.cell(0, 6, f"Date : {date_facture.strftime('%d/%m/%Y')}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(15)

    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(60, 60, 60)

    pdf.cell(95, 12, "  Description", border="TB", fill=True)
    pdf.cell(25, 12, "Qté", border="TB", align="C", fill=True)
    pdf.cell(30, 12, "P.U. HT ", border="TB", align="R", fill=True)
    pdf.cell(30, 12, "Total HT ", border="TB", align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)

    total_ht_global = 0.0

    for index, row in df.iterrows():
        desc = str(row.get('Description', f'Article {index+1}'))
        qte = float(row.get('Quantite', 1))
        prix_u = float(row.get('Prix_Unitaire_HT', 0))
        total_ligne = qte * prix_u
        total_ht_global += total_ligne

        fill = index % 2 == 1
        pdf.set_fill_color(252, 252, 252)

        pdf.cell(95, 10, f"  {desc[:50]}", border="B", fill=fill)
        pdf.cell(25, 10, f"{qte}", border="B", align="C", fill=fill)
        pdf.cell(30, 10, f"{prix_u:,.2f} EUR ", border="B", align="R", fill=fill)
        pdf.cell(30, 10, f"{total_ligne:,.2f} EUR ", border="B", align="R", fill=fill, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    tva = total_ht_global * (taux_tva / 100)
    total_ttc = total_ht_global + tva

    pdf.set_font("helvetica", "", 10)
    pdf.cell(150, 8, "Total HT : ", align="R")
    pdf.cell(30, 8, f"{total_ht_global:,.2f} EUR ", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.cell(150, 8, f"TVA ({taux_tva}%) : ", align="R")
    pdf.cell(30, 8, f"{tva:,.2f} EUR ", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_draw_color(0, 0, 0)
    pdf.cell(150, 12, "NET À PAYER TTC : ", align="R")
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(30, 12, f"{total_ttc:,.2f} EUR ", align="R", fill=True, border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(-60)
    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(80, 80, 80)

    pdf.set_fill_color(248, 249, 250)
    pdf.set_draw_color(230, 230, 230)

    message_complet = f"Note de {nom_entreprise} : {message_ia}"

    current_y = pdf.get_y()
    pdf.rect(15, current_y, 180, 25, style="FD")
    pdf.set_xy(20, current_y + 5)
    pdf.multi_cell(170, 5, message_complet, align="C")

    pdf.set_y(-15)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, f"{nom_entreprise} - Facture générée par PME AI Toolkit", align="C")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name
