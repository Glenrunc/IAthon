"""Interface utilisateur pour le module RH & Recrutement."""

from __future__ import annotations

import streamlit as st

from core.pdf_reader import read_text
from core.rh import analyser_candidature


def render_rh_view() -> None:
    """Affiche l'interface du module RH & Recrutement."""
    st.header("🤝 Assistant RH & Recrutement")
    st.write("Analysez la compatibilité d'un candidat avec un poste en quelques secondes.")

    if 'rh_result' in st.session_state and st.session_state.get('rh_result'):
        st.success("📋 Analyse précédente (affichée depuis le cache)")
        st.markdown("### 📊 Résultat de l'analyse")
        st.info(st.session_state['rh_result'])
        st.divider()

    col1, col2 = st.columns(2)
    with col1:
        description_poste = st.text_area(
            "Description du poste",
            height=200,
            placeholder="Missions, compétences requises, profil recherché...",
            key="rh_description_poste"
        )
    with col2:
        cv_file = st.file_uploader("Téléverser le CV (PDF)", type=["pdf"], key="rh_cv_upload")

    if st.button("Analyser la candidature ✨", type="primary"):
        if not description_poste or not cv_file:
            st.warning("Veuillez fournir la description du poste et le CV.")
            return

        with st.spinner("Analyse du profil en cours..."):
            cv_bytes = cv_file.read()
            cv_texte = read_text(cv_bytes) or ""
            if not cv_texte:
                st.error("Impossible d'extraire le texte du CV. Vérifiez que le fichier contient du texte extractible.")
                return
            analyse = analyser_candidature(description_poste, cv_texte)
            st.session_state['rh_result'] = analyse
            st.rerun()
