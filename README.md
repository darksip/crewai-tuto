# CrewAI Veille Simple

Système de veille automatisée **ultra-simple** avec CrewAI. Configuration 100% déclarative via YAML + gestion des secrets avec Doppler.

## 📁 Structure (4 fichiers seulement !)

```
crewai-veille-simple/
├── veille.yaml      # ⚙️  Configuration complète 
├── main.py          # 🚀 Script principal (200 lignes)
├── pyproject.toml   # 📦 Dépendances minimales (3 packages)
└── README.md        # 📖 Documentation
```

## 🚀 Installation

```bash
# Installer les dépendances
uv sync

# Configurer Doppler (une seule fois)
doppler setup
doppler secrets set SERPER_API_KEY "votre-clé-serper"
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

## 🛠️ API Requises

- **Serper API** : Recherche Google (https://serper.dev)
- **OpenAI API** : LLM pour les agents (https://platform.openai.com)

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
| Lignes de code | 3700 | 200 |
| Fichiers Python | 18 | 1 |
| Packages | 84 | 3 |
| Configuration | Code Python | YAML déclaratif |
| Gestion secrets | Variables d'env | Doppler intégré |
| Maintenance | Très difficile | Ultra facile |

**Résultat** : Même fonctionnalité, **18x moins de complexité** ! 🎉