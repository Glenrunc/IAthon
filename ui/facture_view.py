"""Interface utilisateur pour la génération de factures PDF."""

from __future__ import annotations

import datetime
import streamlit as st

import pandas as pd

from core.facture import creer_pdf_facture, generer_message_ia


def render_facture_view() -> None:
    """Affiche l'interface du module Génération de Factures."""
    st.header("📝 Générateur de Factures Pro")
    st.write("Créez des factures élégantes avec une touche personnalisée par l'IA.")

    if 'facture_pdf_path' in st.session_state and st.session_state.get('facture_pdf_path'):
        st.success("📋 Facture précédemment générée (téléchargeable ci-dessous)")
        with open(st.session_state['facture_pdf_path'], "rb") as f:
            st.download_button(
                label="📥 Télécharger la Facture PDF",
                data=f.read(),
                file_name=st.session_state.get('facture_nom', 'Facture.pdf'),
                mime='application/pdf'
            )
        st.divider()

    col1, col2 = st.columns(2)
    with col1:
        client_nom = st.text_input("Client", "Client Exemple SAS", key="facture_client")
        num_facture = st.text_input("N° Facture", "FAC-2026-001", key="facture_num")
    with col2:
        date_facture = st.date_input("Date", datetime.date.today(), key="facture_date")
        taux_tva = st.number_input("TVA (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.1, key="facture_tva")

    st.divider()

    fichier_upload = st.file_uploader("Lignes de facturation (CSV/Excel)", type=['csv', 'xlsx'], key="facture_upload")

    if fichier_upload is not None:
        try:
            if fichier_upload.name.endswith('.csv'):
                df = pd.read_csv(fichier_upload)
            else:
                df = pd.read_excel(fichier_upload)

            st.session_state['facture_df'] = df

            st.dataframe(df, use_container_width=True)

            if st.button("Générer le PDF Premium ✨", type="primary"):
                with st.spinner("L'IA rédige votre mot et met en page le document..."):
                    nom_entreprise = st.session_state.get('entreprise_nom', 'Ma PME')
                    gerant_nom = st.session_state.get('entreprise_gerant', '')
                    logo_path = "assets/logo_entreprise.png"

                    message_ia = generer_message_ia(df, client_nom, nom_entreprise)
                    pdf_path = creer_pdf_facture(
                        df, client_nom, num_facture, date_facture,
                        message_ia, taux_tva, nom_entreprise, gerant_nom, logo_path
                    )

                    st.session_state['facture_pdf_path'] = pdf_path
                    st.session_state['facture_nom'] = f"Facture_{num_facture}.pdf"
                    st.rerun()

        except Exception as e:
            st.error(f"Erreur : {e}")
