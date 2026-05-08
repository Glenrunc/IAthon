"""Interface utilisateur pour le module Marketing."""

from __future__ import annotations

import streamlit as st

from core.marketing import generer_contenu_marketing


def render_marketing_view() -> None:
    """Affiche l'interface du module Marketing."""
    st.header("🚀 Générateur de Fiches Produits")
    st.write("Transformez de simples mots-clés en contenu marketing percutant.")

    if 'marketing_result' in st.session_state and st.session_state.get('marketing_result'):
        st.success("📋 Résultat précédent (affiché depuis le cache)")
        resultat = st.session_state['marketing_result']

        if resultat.get('fiche'):
            st.subheader("📝 Fiche Produit")
            st.info(resultat['fiche'])

        if resultat.get('social'):
            st.subheader("📱 Post Réseaux Sociaux")
            st.success(resultat['social'])

        if resultat.get('nom_produit'):
            st.caption(f"Produit : {resultat['nom_produit']}")

        st.divider()

    col1, col2 = st.columns(2)
    with col1:
        nom_produit = st.text_input(
            "Nom du produit",
            placeholder="Ex: Chaise Ergonomique Pro",
            key="marketing_nom_produit"
        )
    with col2:
        public_cible = st.text_input(
            "Public cible (optionnel)",
            placeholder="Ex: Télétravailleurs",
            key="marketing_public_cible"
        )

    caracteristiques = st.text_area(
        "Caractéristiques brutes",
        placeholder="Ex: bois de chêne, réglages en hauteur, assise mesh, accoudoirs réglables, design moderne",
        key="marketing_caracteristiques"
    )

    if st.button("Générer le contenu", type="primary"):
        if not nom_produit or not caracteristiques:
            st.warning("Veuillez renseigner le nom du produit et ses caractéristiques.")
            return

        with st.spinner("Création du contenu marketing..."):
            nom_entreprise = st.session_state.get('entreprise_nom', 'notre entreprise')
            resultat = generer_contenu_marketing(nom_produit, public_cible, caracteristiques, nom_entreprise)
            st.session_state['marketing_result'] = resultat
            st.rerun()
