"""Interface utilisateur pour le module Service Client."""

from __future__ import annotations

import streamlit as st

from core.client import analyser_avis_client


def render_client_view() -> None:
    """Affiche l'interface du module Service Client."""
    st.header("💬 Copilote Service Client")
    st.write("Analysez les avis de vos clients et générez des réponses professionnelles en un clic.")

    if 'client_result' in st.session_state and st.session_state.get('client_result'):
        st.success("📋 Résultat précédent (affiché depuis le cache)")
        resultat = st.session_state['client_result']

        st.subheader("Analyse du Sentiment")
        sentiment = resultat.get('sentiment', '')
        if "Positif" in sentiment:
            st.success(sentiment)
        elif "Négatif" in sentiment:
            st.error(sentiment)
        else:
            st.info(sentiment)

        st.subheader("Brouillon de réponse (à valider)")
        st.text_area(
            "Vous pouvez modifier la réponse avant de la copier :",
            value=resultat.get('brouillon', ''),
            height=200,
            key="client_reponse_cachee"
        )

        st.divider()

    avis_client = st.text_area(
        "Collez l'avis client ici :",
        height=150,
        placeholder="Ex: Le produit est arrivé en retard et l'emballage était abîmé, je suis très déçu...",
        key="client_avis_input"
    )

    if st.button("Analyser et générer une réponse", type="primary"):
        if not avis_client:
            st.warning("Veuillez entrer un avis client.")
            return

        with st.spinner("Analyse en cours..."):
            nom_entreprise = st.session_state.get('entreprise_nom', 'la PME')
            nom_gerant = st.session_state.get('entreprise_gerant', 'Le gérant')
            resultat = analyser_avis_client(avis_client, nom_entreprise, nom_gerant)
            st.session_state['client_result'] = resultat
            st.rerun()
