"""Interface utilisateur pour le module Audio."""

from __future__ import annotations

import streamlit as st

from core.audio import generer_compte_rendu_reunion


def render_audio_view() -> None:
    """Affiche l'interface du module Audio."""
    st.header("🎙️ Compte-rendu de Réunion Express")
    st.write("Téléversez l'enregistrement de votre réunion pour obtenir un résumé structuré et les actions à entreprendre.")

    if 'audio_result' in st.session_state and st.session_state.get('audio_result'):
        st.success("📋 Compte-rendu précédent (affiché depuis le cache)")
        st.markdown("### 📝 Compte-rendu Généré")
        st.success(st.session_state['audio_result'])
        st.divider()

    audio_file = st.file_uploader("Fichier audio (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"], key="audio_upload")

    if audio_file is not None:
        st.audio(audio_file)

        if st.button("Générer le compte-rendu 📝", type="primary"):
            with st.spinner("L'IA écoute et analyse la réunion... Cela peut prendre un instant selon la durée."):
                audio_bytes = audio_file.read()
                resultat = generer_compte_rendu_reunion(audio_bytes, audio_file.type)
                st.session_state['audio_result'] = resultat
                st.rerun()
