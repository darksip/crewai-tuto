#!/usr/bin/env python3
"""
Système de veille CrewAI - Version Simple
Configuration 100% déclarative via YAML
"""

import yaml
import json
import argparse
import feedparser
from datetime import datetime, timedelta
from pathlib import Path

# Imports CrewAI
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool


def load_config(config_file="veille.yaml"):
    """Charger la configuration YAML"""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Fichier {config_file} non trouvé")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Erreur YAML : {e}")
        return None


def create_agents(config):
    """Créer les agents depuis la configuration"""
    agents = {}

    for name, agent_config in config["agents"].items():
        agent = Agent(
            role=agent_config["role"],
            goal=agent_config["goal"],
            backstory=agent_config["backstory"],
            verbose=True,
        )
        agents[name] = agent

    return agents


def extract_channel_name(url):
    """Extraire le nom de la chaîne depuis l'URL YouTube"""
    try:
        if "@" in url:
            # Format: https://www.youtube.com/@Underscore_
            return url.split("@")[-1]
        elif "/c/" in url:
            # Format: https://www.youtube.com/c/Micode
            return url.split("/c/")[-1]
        elif "/channel/" in url:
            # Format: https://www.youtube.com/channel/UCxxx
            return url.split("/channel/")[-1]
        else:
            # Fallback: prendre la dernière partie après /
            return url.split("/")[-1]
    except (IndexError, AttributeError):
        return url  # Retourner l'URL si extraction échoue


def get_channel_id_from_url(channel_url):
    """Obtenir l'ID de la chaîne depuis son URL YouTube - Méthode curl/grep simple"""
    try:
        # Si c'est déjà un ID de chaîne
        if channel_url.startswith("UC") and len(channel_url) == 24:
            return channel_url

        # Si c'est une URL avec /channel/
        if "/channel/" in channel_url:
            return channel_url.split("/channel/")[-1].split("?")[0]

        # Utiliser la méthode curl/grep qui fonctionne parfaitement
        import subprocess

        cmd = f'''curl -sL "{channel_url}" | grep -oE '("channelId"|"externalId"|"ownerChannelId"):"UC[-_0-9A-Za-z]{{22}}' | head -n1 | grep -oE 'UC[-_0-9A-Za-z]{{22}}' '''

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            channel_id = result.stdout.strip()
            if channel_id.startswith("UC") and len(channel_id) == 24:
                return channel_id

        print(f"⚠️ Impossible de trouver l'ID pour {channel_url}")
        return None

    except Exception as e:
        print(f"❌ Erreur extraction ID chaîne {channel_url}: {e}")
        return None


def get_recent_videos_from_rss(channel_url, hours_limit=24):
    """Récupérer les vidéos récentes via RSS feed YouTube"""
    try:
        # Obtenir l'ID de la chaîne
        channel_id = get_channel_id_from_url(channel_url)
        if not channel_id:
            return []

        # Construire l'URL du flux RSS
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        # Parser le flux RSS
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            print(f"⚠️ Aucune vidéo trouvée dans le flux RSS pour {channel_url}")
            return []

        # Filtrer par date (dernières X heures)
        cutoff_time = datetime.now() - timedelta(hours=hours_limit)
        recent_videos = []

        for entry in feed.entries:
            try:
                # Parser la date de publication
                pub_date = datetime(*entry.published_parsed[:6])

                # Garder seulement les vidéos récentes
                if pub_date > cutoff_time:
                    video = {
                        "title": entry.title,
                        "url": entry.link,
                        "published": entry.published,
                        "channel": feed.feed.title
                        if hasattr(feed.feed, "title")
                        else extract_channel_name(channel_url),
                        "description": getattr(entry, "summary", ""),
                        "published_date": pub_date,
                    }
                    recent_videos.append(video)

            except Exception as e:
                print(f"⚠️ Erreur parsing vidéo : {e}")
                continue

        # Trier par date (plus récent en premier)
        recent_videos.sort(key=lambda x: x["published_date"], reverse=True)

        return recent_videos

    except Exception as e:
        print(f"❌ Erreur RSS pour {channel_url} : {e}")
        return []


def create_daily_directory(date):
    """Créer le répertoire daily pour une date donnée"""
    date_str = date.strftime("%Y-%m-%d")
    daily_dir = Path("daily") / date_str
    daily_dir.mkdir(parents=True, exist_ok=True)
    return daily_dir


def get_processed_videos(daily_dir):
    """Récupérer la liste des vidéos déjà traitées pour une date"""
    processed_file = daily_dir / "videos_processed.json"

    if processed_file.exists():
        try:
            with open(processed_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("video_ids", []))
        except Exception as e:
            print(f"⚠️ Erreur lecture videos_processed.json : {e}")

    return set()


def save_processed_video(daily_dir, video):
    """Sauvegarder une vidéo comme traitée dans son répertoire daily"""
    processed_file = daily_dir / "videos_processed.json"

    # Charger les vidéos déjà traitées
    processed_data = {"video_ids": [], "videos": []}
    if processed_file.exists():
        try:
            with open(processed_file, "r", encoding="utf-8") as f:
                processed_data = json.load(f)
        except Exception:
            pass

    # Ajouter la nouvelle vidéo si pas déjà présente
    video_id = (
        video["url"].split("watch?v=")[-1].split("&")[0]
    )  # Extraire l'ID de la vidéo

    if video_id not in processed_data["video_ids"]:
        processed_data["video_ids"].append(video_id)
        processed_data["videos"].append(
            {
                "video_id": video_id,
                "title": video["title"],
                "url": video["url"],
                "channel": video["channel"],
                "published": video["published"],
                "processed_at": datetime.now().isoformat(),
            }
        )

        # Sauvegarder
        try:
            with open(processed_file, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erreur sauvegarde video processée : {e}")


def get_all_youtube_videos(topic):
    """Récupérer toutes les vidéos récentes pour un topic via RSS (7 jours) et vérifier déjà traitées"""
    all_videos = []
    new_videos_count = 0

    print(f"📡 Récupération RSS pour {topic['name']} (7 derniers jours)...")

    for channel_url in topic["youtube_channels"]:
        channel_name = extract_channel_name(channel_url)
        print(f"  📺 Analyse de {channel_name}...")

        videos = get_recent_videos_from_rss(
            channel_url, hours_limit=168
        )  # 7 jours = 168 heures

        if videos:
            print(f"    📊 {len(videos)} vidéo(s) trouvée(s) sur 7 jours")

            # Trier par date de publication pour traiter par jour
            for video in videos:
                pub_date = video["published_date"].date()  # Date seulement, sans heure
                daily_dir = create_daily_directory(pub_date)

                # Vérifier si déjà traitée
                processed_videos = get_processed_videos(daily_dir)
                video_id = video["url"].split("watch?v=")[-1].split("&")[0]

                if video_id not in processed_videos:
                    video["daily_dir"] = daily_dir
                    video["video_id"] = video_id
                    all_videos.append(video)
                    new_videos_count += 1
                    print(
                        f"    🆕 Nouvelle vidéo pour {pub_date}: {video['title'][:50]}..."
                    )
                else:
                    print(f"    ⏭️  Déjà traitée ({pub_date}): {video['title'][:50]}...")
        else:
            print("    ⚠️ Aucune vidéo trouvée")

    print(f"📈 Total : {new_videos_count} nouvelles vidéos à traiter")

    # Trier par date de publication (plus récent en premier)
    all_videos.sort(key=lambda x: x["published_date"], reverse=True)
    return all_videos


def create_tasks(config, agents, topic):
    """Créer les tâches pour un topic donné"""
    tasks = []

    # Préparer les variables pour le formatage
    variables = {
        "topic_name": topic["name"],
        "keywords": ", ".join(topic["keywords"]),
        "youtube_channels": ", ".join(topic["youtube_channels"]),  # URLs complètes
        "volume": topic["volume"],
        "date": datetime.now().strftime("%d/%m/%Y"),
    }

    # Créer les tâches depuis la config
    for task_name, task_config in config["tasks"].items():
        task = Task(
            description=task_config["description"].format(**variables),
            expected_output=task_config["expected_output"],
            agent=agents[task_config["agent"]],
        )
        tasks.append(task)

    return tasks


def save_synthesis(synthesis_content, topic_name, output_dir="syntheses"):
    """Sauvegarder la synthèse"""
    # Créer le répertoire s'il n'existe pas
    Path(output_dir).mkdir(exist_ok=True)

    # Nom du fichier avec date
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{output_dir}/synthese_{topic_name.replace(' ', '_')}_{date_str}.md"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(synthesis_content)
        print(f"✅ Synthèse sauvée : {filename}")
        return filename
    except Exception as e:
        print(f"❌ Erreur sauvegarde : {e}")
        return None


def run_veille_for_topic(config, agents, topic):
    """Exécuter la veille pour un topic avec persistence par date de publication"""
    print(f"\n🚀 Traitement du topic : {topic['name']}")

    # Étape 1: Récupérer les nouvelles vidéos (7 jours, vérification déjà traitées)
    new_videos = get_all_youtube_videos(topic)

    if not new_videos:
        print("ℹ️ Aucune nouvelle vidéo à traiter")
        return None

    # Grouper les vidéos par date de publication
    videos_by_date = {}
    for video in new_videos:
        pub_date = video["published_date"].date()
        if pub_date not in videos_by_date:
            videos_by_date[pub_date] = []
        videos_by_date[pub_date].append(video)

    print(f"📅 Vidéos réparties sur {len(videos_by_date)} jour(s)")

    processed_syntheses = []

    # Traiter chaque jour séparément
    for pub_date, date_videos in sorted(videos_by_date.items(), reverse=True):
        print(f"\n📆 Traitement des vidéos du {pub_date} ({len(date_videos)} vidéos)")

        # Préparer le contexte pour cette date
        videos_context = f"\n\nVIDÉOS YOUTUBE DU {pub_date} :\n"
        for i, video in enumerate(date_videos, 1):
            videos_context += f"{i}. **{video['title']}** ({video['channel']})\n"
            videos_context += f"   URL: {video['url']}\n"
            videos_context += f"   Publié: {video['published']}\n"
            if video["description"]:
                videos_context += f"   Description: {video['description'][:100]}...\n"
            videos_context += "\n"

        # Créer les tâches avec contexte spécifique à cette date
        tasks = create_tasks_with_video_context(
            config, agents, topic, videos_context, pub_date
        )

        # Ajouter l'outil Serper aux agents
        search_tool = SerperDevTool()
        for agent in agents.values():
            agent.tools = [search_tool]

        # Créer et lancer le crew
        crew = Crew(agents=list(agents.values()), tasks=tasks, verbose=True)

        try:
            print(f"⚡ Lancement analyse pour {pub_date}...")
            result = crew.kickoff()

            # Sauvegarder la synthèse dans le répertoire daily de la date de publication
            daily_dir = create_daily_directory(pub_date)
            synthesis_file = (
                daily_dir / f"synthese_{topic['name'].replace(' ', '_')}_{pub_date}.md"
            )

            with open(synthesis_file, "w", encoding="utf-8") as f:
                f.write(str(result))

            # Marquer toutes les vidéos de cette date comme traitées
            for video in date_videos:
                save_processed_video(daily_dir, video)

            print(f"✅ Synthèse {pub_date} sauvée : {synthesis_file}")
            processed_syntheses.append(str(synthesis_file))

        except Exception as e:
            print(f"❌ Erreur traitement {pub_date} : {e}")

    print(
        f"\n🎉 Traitement terminé : {len(processed_syntheses)} synthèse(s) générée(s)"
    )
    return processed_syntheses


def create_tasks_with_video_context(
    config, agents, topic, videos_context, pub_date=None
):
    """Créer les tâches avec le contexte vidéos pré-récupéré pour une date spécifique"""
    tasks = []

    # Utiliser la date de publication ou aujourd'hui
    target_date = pub_date if pub_date else datetime.now().date()

    # Préparer les variables pour le formatage
    variables = {
        "topic_name": topic["name"],
        "keywords": ", ".join(topic["keywords"]),
        "youtube_channels": ", ".join(topic["youtube_channels"]),
        "volume": topic["volume"],
        "date": target_date.strftime("%d/%m/%Y"),
        "videos_context": videos_context,
    }

    # Créer les tâches depuis la config
    for task_name, task_config in config["tasks"].items():
        description = task_config["description"].format(**variables)

        # Pour la tâche de synthèse, ajouter le contexte vidéos
        if task_name == "synthesize" and videos_context:
            description += videos_context

        task = Task(
            description=description,
            expected_output=task_config["expected_output"],
            agent=agents[task_config["agent"]],
        )
        tasks.append(task)

    return tasks


def main():
    parser = argparse.ArgumentParser(description="Veille CrewAI Simple")
    parser.add_argument(
        "--config", default="veille.yaml", help="Fichier de configuration"
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
        print("🧪 Test des flux RSS YouTube...")
        print("=" * 50)

        for topic in config["topics"]:
            print(f"\n📺 Topic : {topic['name']}")
            videos = get_all_youtube_videos(topic)

            if videos:
                print(f"✅ {len(videos)} vidéo(s) récente(s) :")
                for video in videos[:3]:  # Afficher les 3 premières
                    print(f"  • {video['title']}")
                    print(
                        f"    Chaîne: {video['channel']} | Publié: {video['published']}"
                    )
                    print(f"    URL: {video['url']}")
                    print()
            else:
                print("⚠️ Aucune vidéo récente trouvée")

        return 0

    # Afficher le statut des répertoires daily
    if args.status_daily:
        print("📊 Statut des répertoires daily...")
        print("=" * 50)

        daily_base = Path("daily")
        if not daily_base.exists():
            print("⚠️ Aucun répertoire daily trouvé")
            return 0

        # Parcourir les répertoires de dates
        date_dirs = sorted(
            [d for d in daily_base.iterdir() if d.is_dir()], reverse=True
        )

        if not date_dirs:
            print("⚠️ Aucun répertoire de date trouvé")
            return 0

        for date_dir in date_dirs[:10]:  # 10 derniers jours
            date_name = date_dir.name
            print(f"\n📅 {date_name}")

            # Compter les vidéos traitées
            processed_file = date_dir / "videos_processed.json"
            video_count = 0
            if processed_file.exists():
                try:
                    with open(processed_file, "r") as f:
                        data = json.load(f)
                        video_count = len(data.get("video_ids", []))
                except Exception:
                    pass

            # Compter les synthèses
            synthesis_files = list(date_dir.glob("synthese_*.md"))

            print(f"  📹 Vidéos traitées : {video_count}")
            print(f"  📝 Synthèses : {len(synthesis_files)}")

            if synthesis_files:
                for synth_file in synthesis_files:
                    print(f"    • {synth_file.name}")

        return 0

    # Note: Les API keys sont gérées par Doppler automatiquement

    if args.dry_run:
        print("🧪 Mode simulation - Pas d'appels API")
        return 0

    # Créer les agents
    agents = create_agents(config)
    print(f"🎭 {len(agents)} agents créés : {', '.join(agents.keys())}")

    # Traitement des topics
    topics_to_process = config["topics"]

    # Filtrer par topic si spécifié
    if args.topic:
        topics_to_process = [
            t for t in topics_to_process if t["name"].lower() == args.topic.lower()
        ]
        if not topics_to_process:
            print(f"❌ Topic '{args.topic}' non trouvé")
            return 1

    # Traiter chaque topic
    results = []
    for topic in topics_to_process:
        filename = run_veille_for_topic(config, agents, topic)
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
