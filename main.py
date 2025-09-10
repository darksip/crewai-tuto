#!/usr/bin/env python3
"""
TUTORIEL CREWAI - Système de veille automatisée avec agents IA

Ce projet sert d'exemple complet d'utilisation de CrewAI 2025 pour :
- Orchestrer plusieurs agents IA spécialisés
- Utiliser les decorators modernes (@CrewBase, @agent, @task)
- Intégrer des sources de données externes (RSS, API)
- Organiser le traitement par date avec persistence
- Gérer la configuration via fichiers YAML séparés

Architecture démontrée :
- VeilleCrew : Équipe d'agents avec decorators
- YouTube RSS : Collecte automatique de vidéos
- Daily persistence : Évitement des doublons par date
- CLI complète : Interface utilisateur intuitive
"""

import yaml
import argparse

# TUTORIEL: Imports des modules du projet
from veille_crew import VeilleCrew  # Classe principale avec decorators CrewAI
from youtube_processor import (
    collect_videos_for_topic,
    test_rss_feeds,
    extract_channel_name,
)  # Logique YouTube
from daily_manager import (  # Gestion persistence quotidienne
    filter_new_videos,
    group_videos_by_date,
    save_synthesis_by_date,
    mark_videos_as_processed,
    display_daily_status,
)


def load_config(config_file="config/topics.yaml"):
    """Charger la configuration des topics"""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Fichier {config_file} non trouvé")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Erreur YAML : {e}")
        return None


def run_veille_for_topic(topic):
    """
    TUTORIEL: Pipeline principal de traitement d'un topic

    Cette fonction montre l'orchestration niveau métier :
    1. Collecte des données (YouTube RSS)
    2. Filtrage intelligent (éviter doublons)
    3. Organisation par date (daily/)
    4. Traitement par VeilleCrew (agents IA)
    """
    print(f"\n🚀 Traitement du topic : {topic['name']}")

    # TUTORIEL: Étape 1 - Collecte des données externes
    # youtube_processor récupère 7 jours de vidéos via flux RSS natifs
    all_videos = collect_videos_for_topic(topic)

    # TUTORIEL: Étape 2 - Intelligence de filtrage
    # daily_manager vérifie quelles vidéos n'ont pas encore été traitées
    new_videos = filter_new_videos(all_videos)

    if not new_videos:
        print("ℹ️ Aucune nouvelle vidéo à traiter")
        return None

    # TUTORIEL: Étape 3 - Organisation par date de publication
    # Chaque vidéo sera traitée dans daily/sa-date-publication/
    videos_by_date = group_videos_by_date(new_videos)
    print(f"📅 Vidéos réparties sur {len(videos_by_date)} jour(s)")

    processed_syntheses = []

    # TUTORIEL: Traitement séparé par date - Pattern important
    # Permet de créer des synthèses historiques cohérentes
    for pub_date, date_videos in sorted(videos_by_date.items(), reverse=True):
        print(f"\n📆 Traitement des vidéos du {pub_date} ({len(date_videos)} vidéos)")

        # TUTORIEL: Délégation au système d'agents CrewAI
        synthesis_file = process_date_videos(topic, pub_date, date_videos)

        if synthesis_file:
            processed_syntheses.append(synthesis_file)

    print(
        f"\n🎉 Traitement terminé : {len(processed_syntheses)} synthèse(s) générée(s)"
    )
    return processed_syntheses


def process_date_videos(topic, pub_date, date_videos):
    """
    TUTORIEL: Traitement par équipe d'agents CrewAI

    Cette fonction montre comment utiliser la classe VeilleCrew
    avec les decorators modernes pour traiter des données spécifiques.
    """
    # TUTORIEL: Préparation du contexte pour les agents IA
    # Les agents ont besoin de connaître les vidéos à analyser
    videos_context = f"\n\nVIDÉOS YOUTUBE DU {pub_date} :\n"
    for i, video in enumerate(date_videos, 1):
        videos_context += f"{i}. **{video['title']}** ({video['channel']})\n"
        videos_context += f"   URL: {video['url']}\n"
        videos_context += f"   Publié: {video['published']}\n"
        if video["description"]:
            videos_context += f"   Description: {video['description'][:100]}...\n"
        videos_context += "\n"

    try:
        print(f"⚡ Lancement VeilleCrew pour {pub_date}...")

        # TUTORIEL: Instanciation et lancement de l'équipe d'agents
        # VeilleCrew.create_for_topic() utilise le pattern Factory
        crew_instance = VeilleCrew.create_for_topic(topic, videos_context, pub_date)

        # TUTORIEL: kickoff_for_topic() démarre l'exécution séquentielle
        # 1. Agent researcher → cherche articles avec Serper
        # 2. Agent synthesizer → crée synthèse avec articles + vidéos
        result = crew_instance.kickoff_for_topic(topic, videos_context, pub_date)

        # TUTORIEL: Persistence du résultat dans l'organisation daily/
        synthesis_file = save_synthesis_by_date(str(result), topic["name"], pub_date)

        # TUTORIEL: Marquage anti-doublons pour éviter retraitement
        mark_videos_as_processed(date_videos)

        return synthesis_file

    except Exception as e:
        print(f"❌ Erreur traitement VeilleCrew {pub_date} : {e}")
        return None


def main():
    """
    TUTORIEL: Interface CLI pour le système de veille

    Cette fonction montre comment créer une interface utilisateur
    pour un système CrewAI avec différents modes de fonctionnement.
    """
    # TUTORIEL: Configuration CLI avec argparse
    parser = argparse.ArgumentParser(
        description="Veille CrewAI Simple - Tutoriel complet"
    )
    parser.add_argument(
        "--config", default="config/topics.yaml", help="Fichier de configuration topics"
    )
    parser.add_argument("--topic", help="Topic spécifique à traiter")
    parser.add_argument("--list-topics", action="store_true", help="Lister les topics")
    parser.add_argument(
        "--test-rss", action="store_true", help="Tester les flux RSS YouTube"
    )
    parser.add_argument(
        "--status-daily",
        action="store_true",
        help="Afficher le statut des répertoires daily",
    )
    parser.add_argument("--dry-run", action="store_true", help="Mode simulation")

    args = parser.parse_args()

    # Banner
    print("""
╔══════════════════════════════════════════════════╗
║            🤖 CrewAI Veille Simple               ║
║                                                  ║
║        Configuration 100% déclarative           ║
╚══════════════════════════════════════════════════╝
    """)

    # Charger la configuration
    config = load_config(args.config)
    if not config:
        return 1

    # Lister les topics
    if args.list_topics:
        print("📋 Topics configurés :")
        for topic in config["topics"]:
            # Extraire les noms des chaînes pour l'affichage
            channel_names = [
                extract_channel_name(url) for url in topic["youtube_channels"]
            ]

            print(f"  • {topic['name']} (volume: {topic['volume']})")
            print(f"    Mots-clés : {', '.join(topic['keywords'])}")
            print(f"    Chaînes YouTube : {', '.join(channel_names)}")
            print()
        return 0

    # Tester les flux RSS YouTube
    if args.test_rss:
        test_rss_feeds(config["topics"])
        return 0

    # Afficher le statut des répertoires daily
    if args.status_daily:
        display_daily_status()
        return 0

    # Note: Les API keys sont gérées par Doppler automatiquement

    if args.dry_run:
        print("🧪 Mode simulation - Pas d'appels API")
        return 0

    # Traitement des topics avec VeilleCrew moderne
    topics_to_process = config["topics"]

    # Filtrer par topic si spécifié
    if args.topic:
        topics_to_process = [
            t for t in topics_to_process if t["name"].lower() == args.topic.lower()
        ]
        if not topics_to_process:
            print(f"❌ Topic '{args.topic}' non trouvé")
            return 1

    print("🎭 Utilisation VeilleCrew avec decorators @agent/@task/@crew")

    # TUTORIEL: Traitement de chaque topic avec CrewAI
    # Chaque topic génère potentiellement plusieurs synthèses (une par date de publication)
    results = []
    for topic in topics_to_process:
        # TUTORIEL: run_veille_for_topic() orchestrera les agents IA
        # pour ce topic spécifique en utilisant VeilleCrew
        filename = run_veille_for_topic(topic)
        if filename:
            results.append(filename)

    # Résumé
    print("\n🎉 Traitement terminé !")
    print(f"📊 {len(results)} synthèses générées :")
    for filename in results:
        print(f"  📄 {filename}")

    return 0


if __name__ == "__main__":
    exit(main())
