# CrewAI Veille Simple

Système de veille automatisée **ultra-simple** avec CrewAI. Configuration 100% déclarative via YAML + gestion des secrets avec Doppler.

## 📁 Structure modulaire

```
crewai-veille-simple/
├── veille.yaml         # ⚙️  Configuration complète 
├── main.py             # 🚀 Orchestration CrewAI (289 lignes)
├── youtube_processor.py # 📺 Logique YouTube RSS (171 lignes)  
├── daily_manager.py    # 🗂️  Persistence quotidienne (200 lignes)
├── pyproject.toml      # 📦 Dépendances minimales (5 packages)
├── README.md           # 📖 Documentation
└── daily/              # 📊 Données générées (ignoré par git)
    └── YYYY-MM-DD/     # Organisation par date de publication
```

### 🧩 Séparation des responsabilités
- **main.py** → Mécanique CrewAI pure (agents, tâches, crews)
- **youtube_processor.py** → YouTube RSS, Channel ID, collecte vidéos
- **daily_manager.py** → Persistence, organisation par dates, évitement doublons

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

## ⚙️ Configuration

Tout se configure dans `veille.yaml` :

- **Topics** : Nom, mots-clés, **URLs YouTube complètes** (plus besoin d'IDs !)
- **Agents** : Rôles, objectifs, contexte
- **Tâches** : Description, agent assigné, format de sortie  
- **Paramètres** : Langue, répertoires, planification

### 📺 Configuration des chaînes YouTube

Utilisez directement les **URLs complètes** des chaînes (copiées-collées depuis YouTube) :

```yaml
topics:
  - name: "Intelligence Artificielle"
    keywords: ["IA générative", "LLM", "ChatGPT"]
    youtube_channels:
      - "https://www.youtube.com/@Underscore_"           # Format @
      - "https://www.youtube.com/@MachinelearniaTv"      # Format @  
      - "https://www.youtube.com/c/Micode"               # Format /c/
    volume: 8
```

**Plus simple à configurer** : copiez l'URL depuis votre navigateur !

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

1. **Modifier les topics** : Éditer la section `topics` dans `veille.yaml`
2. **Ajuster les agents** : Modifier les `role`, `goal`, `backstory`
3. **Personnaliser les tâches** : Changer les descriptions et formats
4. **Paramétrer** : Adapter la section `settings`

## 🆚 Comparaison

| Aspect | Version Complexe | Version Simple |
|--------|------------------|----------------|
| Lignes de code | 3700 | 580 |
| Fichiers Python | 18 | 1 |
| Packages | 84 | 5 |
| Configuration | Code Python dispersé | YAML déclaratif |
| Gestion secrets | Variables d'env | Doppler intégré |
| YouTube | API + outils complexes | RSS feeds natifs |
| Persistence | Système complexe | daily/ par date publication |
| Maintenance | Très difficile | Ultra facile |

**Résultat** : **6x moins de complexité** avec persistence intelligente ! 🎉