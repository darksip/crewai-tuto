#!/usr/bin/env python3
"""
Système de veille CrewAI - Version Simple
Configuration 100% déclarative via YAML
"""

import yaml
import argparse

# Imports modules locaux
from veille_crew import VeilleCrew
from youtube_processor import collect_videos_for_topic, test_rss_feeds, extract_channel_name
from daily_manager import (
    filter_new_videos, group_videos_by_date, save_synthesis_by_date,
    mark_videos_as_processed, display_daily_status
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
    """Exécuter la veille pour un topic avec persistence par date de publication"""
    print(f"\n🚀 Traitement du topic : {topic['name']}")

    # Étape 1: Collecter toutes les vidéos YouTube (7 jours)
    all_videos = collect_videos_for_topic(topic)
    
    # Étape 2: Filtrer les nouvelles vidéos (non encore traitées)
    new_videos = filter_new_videos(all_videos)

    if not new_videos:
        print("ℹ️ Aucune nouvelle vidéo à traiter")
        return None

    # Étape 3: Grouper par date de publication
    videos_by_date = group_videos_by_date(new_videos)
    print(f"📅 Vidéos réparties sur {len(videos_by_date)} jour(s)")

    processed_syntheses = []

    # Traiter chaque jour séparément avec VeilleCrew
    for pub_date, date_videos in sorted(videos_by_date.items(), reverse=True):
        print(f"\n📆 Traitement des vidéos du {pub_date} ({len(date_videos)} vidéos)")

        # Créer et exécuter la synthèse pour cette date
        synthesis_file = process_date_videos(topic, pub_date, date_videos)
        
        if synthesis_file:
            processed_syntheses.append(synthesis_file)

    print(f"\n🎉 Traitement terminé : {len(processed_syntheses)} synthèse(s) générée(s)")
    return processed_syntheses


def process_date_videos(topic, pub_date, date_videos):
    """Traiter les vidéos d'une date spécifique avec VeilleCrew moderne"""
    # Préparer le contexte vidéos pour les agents
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
        
        # Créer et lancer le crew moderne avec decorators
        crew_instance = VeilleCrew.create_for_topic(topic, videos_context, pub_date)
        result = crew_instance.kickoff_for_topic(topic, videos_context, pub_date)

        # Sauvegarder via daily_manager
        synthesis_file = save_synthesis_by_date(str(result), topic['name'], pub_date)
        
        # Marquer les vidéos comme traitées
        mark_videos_as_processed(date_videos)
        
        return synthesis_file

    except Exception as e:
        print(f"❌ Erreur traitement VeilleCrew {pub_date} : {e}")
        return None




def main():
    parser = argparse.ArgumentParser(description="Veille CrewAI Simple")
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

    # Traiter chaque topic avec la classe moderne
    results = []
    for topic in topics_to_process:
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
