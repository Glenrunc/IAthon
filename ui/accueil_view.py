"""Interface utilisateur pour la page d'accueil."""

from __future__ import annotations

import streamlit as st


def render_accueil_view() -> None:
    """Affiche la page d'accueil de l'application."""
    nom_entreprise = st.session_state.get('entreprise_nom', 'Ma PME')

    st.title(f"🏢 {nom_entreprise}")
    st.markdown(f"### Bienvenue dans votre Assistant IA 🚀")
    st.write(f"Bonjour **{st.session_state.get('entreprise_gerant', 'Gérant')}**, cet outil centralise plusieurs utilitaires alimentés par l'IA pour simplifier la gestion de votre PME.")

    st.divider()

    st.subheader("📊 Résumé des outils disponibles")

    col1, col2, col3 = st.columns(3)

    modules_info = [
        {
            "categorie": "📊 Gestion",
            "description": "Automatisez la saisie comptable et créez des factures professionnelles.",
            "modules": ["🧾 Pré-saisie Compta", "📝 Générateur de Factures"],
            "couleur": "blue"
        },
        {
            "categorie": "🤝 Ressources",
            "description": "Optimisez votre gestion RH et valorisez vos réunions.",
            "modules": ["🤝 Recrutement RH", "🎙️ Compte-rendu Réunion"],
            "couleur": "green"
        },
        {
            "categorie": "🚀 Croissance",
            "description": "Boostez votre marketing et votre service client.",
            "modules": ["🚀 Fiches Produits", "💬 Copilote Client"],
            "couleur": "orange"
        },
    ]

    for i, info in enumerate(modules_info):
        col = [col1, col2, col3][i]
        with col:
            st.markdown(f"**{info['categorie']}**")
            st.caption(info['description'])
            for mod in info['modules']:
                st.write(f"- {mod}")

    st.divider()

    with st.expander("ℹ️ Comment utiliser cet outil ?"):
        st.markdown("""
        1. **Configurez d'abord** votre entreprise dans l'onglet ⚙️ Configuration
        2. **Naviguez** entre les modules via le menu latéral groupé par catégorie
        3. **Vos résultats** sont automatiquement sauvegardés : vous ne perdrez jamais votre travail en changeant d'onglet
        4. **Les quotas IA** sont limités ; si une erreur survient, patienter quelques secondes avant de réessayer

        *Tous les modules utilisent l'API Google Gemini pour générer du contenu.*
        """)

    with st.expander("🔑 Fonctionnalités principales"):
        st.markdown("""
        | Module | Ce qu'il fait |
        |--------|---------------|
        | 🧾 **Pré-saisie Compta** | Extrait automatiquement les données de vos factures (PDF/image) |
        | 📝 **Générateur de Factures** | Crée des factures PDF élégantes avec message personnalisé par IA |
        | 🤝 **Recrutement RH** | Analyse la compatibilité CV / poste et génère des questions d'entretien |
        | 🎙️ **Compte-rendu Réunion** | Transcrit et structure vos réunions audio |
        | 🚀 **Fiches Produits** | Génère des fiches produit et posts réseaux sociaux |
        | 💬 **Copilote Client** | Analyse le sentiment des avis et prépare des réponses professionnelles |
        """)

    st.divider()
    st.caption("PME AI Toolkit v2.0 | Propulsé par Google Gemini | Hackathon 2026")
