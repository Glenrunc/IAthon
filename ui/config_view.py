"""Interface utilisateur pour le module Configuration."""

from __future__ import annotations

import streamlit as st

from core.config import charger_configuration, sauvegarder_configuration, charger_logo


def render_config_view() -> None:
    """Affiche l'interface du module Configuration."""
    st.header("⚙️ Configuration de l'entreprise")
    st.write("Personnalisez votre assistant IA en renseignant les informations de votre PME. Ces données sont sauvegardées de manière permanente.")

    with st.form("form_config"):
        st.subheader("Informations générales")
        nom = st.text_input("Nom de l'entreprise", value=st.session_state.get('entreprise_nom', 'Ma PME'))
        gerant = st.text_input("Nom du gérant / de la gérante", value=st.session_state.get('entreprise_gerant', 'Le Gérant'))

        st.subheader("Identité visuelle")
        st.info("Le logo s'affichera dans le menu de navigation à gauche.")
        logo_upload = st.file_uploader("Importer le logo (JPG, PNG)", type=['png', 'jpg', 'jpeg'])

        submit = st.form_submit_button("Sauvegarder la configuration")

    if submit:
        st.session_state['entreprise_nom'] = nom
        st.session_state['entreprise_gerant'] = gerant

        try:
            config_data = sauvegarder_configuration(nom, gerant, logo_upload)

            if config_data.get('logo_path'):
                logo = charger_logo(config_data['logo_path'])
                if logo:
                    st.session_state['entreprise_logo'] = logo

            st.success("✅ Configuration sauvegardée de manière permanente !")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde : {e}")
