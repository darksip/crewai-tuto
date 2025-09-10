# CrewAI Veille Simple - 📚 Projet Tutoriel

**Projet d'apprentissage CrewAI 2025** - Système de veille automatisée servant d'exemple complet pour maîtriser :

🎯 **Objectifs pédagogiques** :
- **Decorators modernes** : @CrewBase, @agent, @task, @crew, @tool
- **Architecture modulaire** : Séparation responsabilités, config YAML
- **Intégrations externes** : RSS YouTube, API Serper, persistence
- **Patterns avancés** : Factory methods, auto-découverte, pipeline séquentiel

💡 **Code richement commenté** : Chaque concept CrewAI expliqué avec des commentaires `# TUTORIEL:` détaillés

## 📚 Apprentissage CrewAI

### 🎓 Concepts démontrés dans le code

- **`veille_crew.py`** → Architecture @CrewBase complète avec tous decorators
- **`main.py`** → Orchestration niveau métier et utilisation de VeilleCrew  
- **`config/*.yaml`** → Configuration externe des agents et tâches
- **`youtube_processor.py`** → Intégration de sources externes
- **`daily_manager.py`** → Gestion de la persistence et anti-doublons

### 💭 Questions d'apprentissage

En lisant le code, demandez-vous :
1. **Comment @CrewBase découvre-t-il automatiquement les @agent/@task ?**
2. **Pourquoi séparer agents.yaml de tasks.yaml ?**
3. **Comment les variables {topic_name} sont-elles injectées ?**
4. **Quel est l'avantage de Process.sequential vs hierarchical ?**
5. **Comment créer un nouvel @agent avec ses propres @tool ?**

### 🔍 Points d'attention

- **Auto-découverte** : `self.agents` et `self.tasks` sont automatiquement peuplés
- **Configuration dynamique** : Variables injectées au runtime dans les descriptions
- **Modularité** : Chaque decorator a un rôle spécifique et clairement défini

## 📁 Structure modulaire avec decorators CrewAI 2025

```
crewai-veille-simple/
├── config/
│   ├── topics.yaml      # 🎯 Topics et paramètres métier
│   ├── agents.yaml      # 🤖 Configuration agents CrewAI
│   └── tasks.yaml       # 📋 Configuration tâches CrewAI
├── veille_crew.py       # 🎭 Classe @CrewBase avec decorators (146 lignes)
├── main.py              # 🚀 Orchestration principale (199 lignes)
├── youtube_processor.py # 📺 Logique YouTube RSS (171 lignes)  
├── daily_manager.py     # 🗂️ Persistence quotidienne (200 lignes)
├── pyproject.toml       # 📦 Dépendances (5 packages)
├── README.md            # 📖 Documentation
└── daily/               # 📊 Données générées (ignoré par git)
    └── YYYY-MM-DD/      # Organisation par date de publication
```

### 🧩 Séparation moderne des responsabilités
- **main.py** → CLI et orchestration niveau topic
- **veille_crew.py** → Classe CrewAI avec @agent/@task/@crew/@tool
- **youtube_processor.py** → YouTube RSS, Channel ID, collecte
- **daily_manager.py** → Persistence, organisation par dates  
- **config/** → Configurations YAML séparées par domaine

## 🚀 Installation

```bash
# Installer les dépendances
uv sync

# Configurer Doppler (une seule fois)
doppler setup
doppler secrets set SERP_API_KEY "votre-clé-serper"
doppler secrets set OPENAI_API_KEY "votre-clé-openai"
```

## 🎯 Utilisation avec Doppler

```bash
# Lister les topics configurés
doppler run -- python main.py --list-topics

# Tester les flux RSS YouTube
doppler run -- python main.py --test-rss

# Voir le statut des répertoires daily
doppler run -- python main.py --status-daily

# Traiter tous les topics
doppler run -- python main.py

# Traiter un topic spécifique  
doppler run -- python main.py --topic "Intelligence Artificielle"

# Mode simulation (sans appels API)
doppler run -- python main.py --dry-run
```

## ⚙️ Configuration modulaire

Configuration séparée par domaine dans `config/` :

### 📁 config/topics.yaml - Données métier
```yaml
topics:
  - name: "Intelligence Artificielle"
    keywords: ["IA générative", "LLM", "ChatGPT"]
    youtube_channels:
      - "https://www.youtube.com/@Underscore_"
      - "https://www.youtube.com/@GosuCoder"
    volume: 8
```

### 🤖 config/agents.yaml - Agents CrewAI
```yaml
researcher:
  role: "Chercheur Web Senior"
  goal: "Trouver les actualités les plus récentes"
  backstory: "Expert en recherche d'information..."

synthesizer:
  role: "Rédacteur de Synthèses"  
  goal: "Créer des synthèses claires"
  backstory: "Journaliste tech expérimenté..."
```

### 📋 config/tasks.yaml - Tâches CrewAI
```yaml
search_articles:
  description: "Recherche les actualités sur {topic_name}..."
  agent: researcher
  expected_output: "Liste d'articles structurée..."

synthesize:
  description: "Crée une synthèse complète..."
  agent: synthesizer
  expected_output: "Synthèse markdown finale..."
```

💡 **URLs YouTube** : Utilisez directement les URLs complètes (@username, /c/, /channel/) - copiez depuis votre navigateur !

## 🔄 Fonctionnement du système

### 📡 Récupération intelligente
1. **RSS feeds YouTube** → 15 dernières vidéos par chaîne (7 jours max)
2. **Résolution automatique** → URLs → Channel IDs (curl/grep)
3. **Recherche Serper** → Articles de presse récents

### 🧠 Persistence par date de publication
1. **Chaque vidéo** est traitée dans `daily/sa-date-publication/`
2. **Évite les doublons** → `videos_processed.json` par date
3. **Synthèses datées** → Une par topic par jour de publication
4. **Exécutions multiples** → Seules les nouvelles vidéos sont traitées

### 🎭 Architecture CrewAI moderne (2025)

Le projet suit les **standards CrewAI 2025** avec decorators :

```python
@CrewBase
class VeilleCrew:
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    @tool
    def serper_search(self):
        return SerperDevTool()
    
    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'])
    
    @task  
    def search_articles(self) -> Task:
        return Task(config=self.tasks_config['search_articles'])
    
    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks)
```

**Avantages** : Auto-découverte agents/tâches, configuration séparée, architecture standard

## 📊 Résultats et Organisation

### 🗂️ Structure automatique par date de publication

```
daily/
├── 2025-09-09/
│   ├── videos_processed.json           # Vidéos traitées ce jour
│   └── synthese_Intelligence_Artificielle_2025-09-09.md
├── 2025-09-08/
│   ├── videos_processed.json
│   └── synthese_Crypto_Finance_2025-09-08.md
└── 2025-09-07/
    ├── videos_processed.json
    └── synthese_Tech_Startups_2025-09-07.md
```

### 📹 Système de persistence intelligent

- **Récupération 7 jours** de vidéos RSS par chaîne
- **Traitement par date de publication** (pas d'exécution)
- **Évite les doublons** : chaque vidéo traitée une seule fois
- **Synthèses datées** : une par topic par jour de publication

## 🎭 Agents

1. **Researcher** : Recherche d'actualités et vidéos YouTube
2. **Synthesizer** : Rédaction des synthèses markdown

## 🛠️ API Requises (seulement 2 !)

- **Serper API** : Recherche Google + YouTube via RSS (https://serper.dev)
- **OpenAI API** : LLM pour les agents CrewAI (https://platform.openai.com)

**🎉 Plus besoin de YouTube Data API !** RSS feeds natifs + résolution curl/grep

## 🔄 Automatisation

Pour automatiser l'exécution quotidienne, ajoutez à votre crontab :

```bash
# Tous les jours à 6h00  
0 6 * * * cd /path/to/crewai-veille-simple && doppler run -- python main.py
```

## 📝 Personnalisation

### 🎯 Modifications par fichier
1. **Topics** : Éditer `config/topics.yaml` → Ajouter sujets, chaînes YouTube, mots-clés
2. **Agents** : Modifier `config/agents.yaml` → Ajuster `role`, `goal`, `backstory`  
3. **Tâches** : Adapter `config/tasks.yaml` → Changer descriptions, formats de sortie
4. **Architecture** : Étendre `veille_crew.py` → Ajouter @agent/@task/@tool

### 🔧 Ajout d'un nouvel agent
```python
# Dans veille_crew.py
@agent
def analyzer(self) -> Agent:
    return Agent(config=self.agents_config['analyzer'])
```

```yaml
# Dans config/agents.yaml  
analyzer:
  role: "Analyste de Tendances"
  goal: "Identifier les patterns émergents"
  backstory: "Expert en analyse prédictive..."
```

## 🆚 Comparaison

| Aspect | Version Complexe | Version Simple |
|--------|------------------|----------------|
| Lignes de code | 3700 | 716 (4 modules) |
| Fichiers Python | 18 | 4 |
| Packages | 84 | 5 |
| Configuration | Code Python dispersé | YAML séparés + decorators |
| Gestion secrets | Variables d'env | Doppler intégré |
| YouTube | API + outils complexes | RSS feeds natifs |
| Persistence | Système complexe | daily/ par date publication |
| Architecture | Monolithique | @CrewBase decorators modernes |
| Maintenance | Très difficile | Ultra facile |

**Résultat** : **5x moins de complexité** + architecture CrewAI 2025 ! 🎉