#!/usr/bin/env python3
"""
Système de veille CrewAI - Version Simple
Configuration 100% déclarative via YAML
"""

import yaml
import os
import argparse
import requests
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
import re
import subprocess

# Imports CrewAI
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool

def load_config(config_file="veille.yaml"):
    """Charger la configuration YAML"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
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
    
    for name, agent_config in config['agents'].items():
        agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            verbose=True
        )
        agents[name] = agent
    
    return agents

def extract_channel_name(url):
    """Extraire le nom de la chaîne depuis l'URL YouTube"""
    try:
        if '@' in url:
            # Format: https://www.youtube.com/@Underscore_
            return url.split('@')[-1]
        elif '/c/' in url:
            # Format: https://www.youtube.com/c/Micode  
            return url.split('/c/')[-1]
        elif '/channel/' in url:
            # Format: https://www.youtube.com/channel/UCxxx
            return url.split('/channel/')[-1]
        else:
            # Fallback: prendre la dernière partie après /
            return url.split('/')[-1]
    except:
        return url  # Retourner l'URL si extraction échoue

def get_channel_id_from_url(channel_url):
    """Obtenir l'ID de la chaîne depuis son URL YouTube - Méthode curl/grep simple"""
    try:
        # Si c'est déjà un ID de chaîne
        if channel_url.startswith('UC') and len(channel_url) == 24:
            return channel_url
            
        # Si c'est une URL avec /channel/
        if '/channel/' in channel_url:
            return channel_url.split('/channel/')[-1].split('?')[0]
        
        # Utiliser la méthode curl/grep qui fonctionne parfaitement
        import subprocess
        
        cmd = f'''curl -sL "{channel_url}" | grep -oE '("channelId"|"externalId"|"ownerChannelId"):"UC[-_0-9A-Za-z]{{22}}' | head -n1 | grep -oE 'UC[-_0-9A-Za-z]{{22}}' '''
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            channel_id = result.stdout.strip()
            if channel_id.startswith('UC') and len(channel_id) == 24:
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
                        "channel": feed.feed.title if hasattr(feed.feed, 'title') else extract_channel_name(channel_url),
                        "description": getattr(entry, 'summary', ''),
                        "published_date": pub_date
                    }
                    recent_videos.append(video)
                    
            except Exception as e:
                print(f"⚠️ Erreur parsing vidéo : {e}")
                continue
        
        # Trier par date (plus récent en premier)
        recent_videos.sort(key=lambda x: x['published_date'], reverse=True)
        
        return recent_videos
        
    except Exception as e:
        print(f"❌ Erreur RSS pour {channel_url} : {e}")
        return []

def get_all_youtube_videos(topic):
    """Récupérer toutes les vidéos récentes pour un topic via RSS"""
    all_videos = []
    
    print(f"📡 Récupération RSS pour {topic['name']}...")
    
    for channel_url in topic['youtube_channels']:
        channel_name = extract_channel_name(channel_url)
        print(f"  📺 Analyse de {channel_name}...")
        
        videos = get_recent_videos_from_rss(channel_url, hours_limit=72)  # 3 jours pour voir GosuCoder
        
        if videos:
            print(f"    ✅ {len(videos)} vidéo(s) récente(s) trouvée(s)")
            all_videos.extend(videos)
        else:
            print(f"    ⚠️ Aucune vidéo récente")
    
    # Limiter au volume demandé et trier par pertinence
    all_videos.sort(key=lambda x: x['published_date'], reverse=True)
    return all_videos[:topic['volume']]

def create_tasks(config, agents, topic):
    """Créer les tâches pour un topic donné"""
    tasks = []
    
    # Extraire les noms des chaînes depuis les URLs
    channel_names = [extract_channel_name(url) for url in topic['youtube_channels']]
    
    # Préparer les variables pour le formatage
    variables = {
        'topic_name': topic['name'],
        'keywords': ', '.join(topic['keywords']),
        'youtube_channels': ', '.join(topic['youtube_channels']),  # URLs complètes
        'volume': topic['volume'],
        'date': datetime.now().strftime('%d/%m/%Y')
    }
    
    # Créer les tâches depuis la config
    for task_name, task_config in config['tasks'].items():
        task = Task(
            description=task_config['description'].format(**variables),
            expected_output=task_config['expected_output'],
            agent=agents[task_config['agent']]
        )
        tasks.append(task)
    
    return tasks

def save_synthesis(synthesis_content, topic_name, output_dir="syntheses"):
    """Sauvegarder la synthèse"""
    # Créer le répertoire s'il n'existe pas
    Path(output_dir).mkdir(exist_ok=True)
    
    # Nom du fichier avec date
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"{output_dir}/synthese_{topic_name.replace(' ', '_')}_{date_str}.md"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(synthesis_content)
        print(f"✅ Synthèse sauvée : {filename}")
        return filename
    except Exception as e:
        print(f"❌ Erreur sauvegarde : {e}")
        return None

def run_veille_for_topic(config, agents, topic):
    """Exécuter la veille pour un topic"""
    print(f"\n🚀 Traitement du topic : {topic['name']}")
    
    # Étape 1: Récupérer les vidéos récentes via RSS (plus fiable que Serper pour YouTube)
    recent_videos = get_all_youtube_videos(topic)
    
    # Préparer le contexte vidéos pour les agents
    videos_context = ""
    if recent_videos:
        videos_context = "\n\nVIDÉOS YOUTUBE RÉCENTES TROUVÉES :\n"
        for i, video in enumerate(recent_videos[:5], 1):
            videos_context += f"{i}. **{video['title']}** ({video['channel']})\n"
            videos_context += f"   URL: {video['url']}\n"
            videos_context += f"   Publié: {video['published']}\n"
            if video['description']:
                videos_context += f"   Description: {video['description'][:100]}...\n"
            videos_context += "\n"
    
    # Créer les tâches avec le contexte vidéos
    tasks = create_tasks_with_video_context(config, agents, topic, videos_context)
    
    # Ajouter l'outil Serper aux agents (pour les articles seulement)
    search_tool = SerperDevTool()
    
    # Assigner l'outil Serper à tous les agents
    for agent in agents.values():
        agent.tools = [search_tool]
    
    # Créer et lancer le crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=True
    )
    
    try:
        # Lancer l'exécution
        print(f"⚡ Lancement du crew pour {topic['name']} avec {len(recent_videos)} vidéos RSS...")
        result = crew.kickoff()
        
        # Sauvegarder le résultat
        output_dir = config.get('settings', {}).get('output_dir', 'syntheses')
        filename = save_synthesis(str(result), topic['name'], output_dir)
        
        print(f"✅ Topic {topic['name']} terminé")
        return filename
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement de {topic['name']} : {e}")
        return None

def create_tasks_with_video_context(config, agents, topic, videos_context):
    """Créer les tâches avec le contexte vidéos pré-récupéré"""
    tasks = []
    
    # Extraire les noms des chaînes depuis les URLs
    channel_names = [extract_channel_name(url) for url in topic['youtube_channels']]
    
    # Préparer les variables pour le formatage
    variables = {
        'topic_name': topic['name'],
        'keywords': ', '.join(topic['keywords']),
        'youtube_channels': ', '.join(topic['youtube_channels']),
        'volume': topic['volume'],
        'date': datetime.now().strftime('%d/%m/%Y'),
        'videos_context': videos_context
    }
    
    # Créer les tâches depuis la config
    for task_name, task_config in config['tasks'].items():
        description = task_config['description'].format(**variables)
        
        # Pour la tâche de synthèse, ajouter le contexte vidéos
        if task_name == 'synthesize' and videos_context:
            description += videos_context
        
        task = Task(
            description=description,
            expected_output=task_config['expected_output'],
            agent=agents[task_config['agent']]
        )
        tasks.append(task)
    
    return tasks

def main():
    parser = argparse.ArgumentParser(description="Veille CrewAI Simple")
    parser.add_argument("--config", default="veille.yaml", help="Fichier de configuration")
    parser.add_argument("--topic", help="Topic spécifique à traiter")
    parser.add_argument("--list-topics", action="store_true", help="Lister les topics")
    parser.add_argument("--test-rss", action="store_true", help="Tester les flux RSS YouTube")
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
        for topic in config['topics']:
            # Extraire les noms des chaînes pour l'affichage
            channel_names = [extract_channel_name(url) for url in topic['youtube_channels']]
            
            print(f"  • {topic['name']} (volume: {topic['volume']})")
            print(f"    Mots-clés : {', '.join(topic['keywords'])}")
            print(f"    Chaînes YouTube : {', '.join(channel_names)}")
            print()
        return 0
    
    # Tester les flux RSS YouTube
    if args.test_rss:
        print("🧪 Test des flux RSS YouTube...")
        print("=" * 50)
        
        for topic in config['topics']:
            print(f"\n📺 Topic : {topic['name']}")
            videos = get_all_youtube_videos(topic)
            
            if videos:
                print(f"✅ {len(videos)} vidéo(s) récente(s) :")
                for video in videos[:3]:  # Afficher les 3 premières
                    print(f"  • {video['title']}")
                    print(f"    Chaîne: {video['channel']} | Publié: {video['published']}")
                    print(f"    URL: {video['url']}")
                    print()
            else:
                print("⚠️ Aucune vidéo récente trouvée")
                
        return 0
    
    # Note: Les API keys sont gérées par Doppler automatiquement
    
    if args.dry_run:
        print("🧪 Mode simulation - Pas d'appels API")
        return 0
    
    # Créer les agents
    agents = create_agents(config)
    print(f"🎭 {len(agents)} agents créés : {', '.join(agents.keys())}")
    
    # Traitement des topics
    topics_to_process = config['topics']
    
    # Filtrer par topic si spécifié
    if args.topic:
        topics_to_process = [t for t in topics_to_process if t['name'].lower() == args.topic.lower()]
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
    print(f"\n🎉 Traitement terminé !")
    print(f"📊 {len(results)} synthèses générées :")
    for filename in results:
        print(f"  📄 {filename}")
    
    return 0

if __name__ == "__main__":
    exit(main())