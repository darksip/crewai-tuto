#!/usr/bin/env python3
"""
Système de veille CrewAI - Version Simple
Configuration 100% déclarative via YAML
"""

import yaml
import os
import argparse
from datetime import datetime
from pathlib import Path

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

def create_tasks(config, agents, topic):
    """Créer les tâches pour un topic donné"""
    tasks = []
    
    # Préparer les variables pour le formatage
    variables = {
        'topic_name': topic['name'],
        'keywords': ', '.join(topic['keywords']),
        'youtube_channels': ', '.join(topic['youtube_channels']),
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
    
    # Créer les tâches
    tasks = create_tasks(config, agents, topic)
    
    # Ajouter l'outil Serper aux agents (un seul outil pour tout !)
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
        print(f"⚡ Lancement du crew pour {topic['name']}...")
        result = crew.kickoff()
        
        # Sauvegarder le résultat
        output_dir = config.get('settings', {}).get('output_dir', 'syntheses')
        filename = save_synthesis(str(result), topic['name'], output_dir)
        
        print(f"✅ Topic {topic['name']} terminé")
        return filename
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement de {topic['name']} : {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Veille CrewAI Simple")
    parser.add_argument("--config", default="veille.yaml", help="Fichier de configuration")
    parser.add_argument("--topic", help="Topic spécifique à traiter")
    parser.add_argument("--list-topics", action="store_true", help="Lister les topics")
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
            print(f"  • {topic['name']} (volume: {topic['volume']})")
            print(f"    Mots-clés : {', '.join(topic['keywords'])}")
            print(f"    Chaînes : {len(topic['youtube_channels'])} chaînes YouTube")
            print()
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