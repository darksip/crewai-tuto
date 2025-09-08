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
doppler secrets set SERP_API_KEY "votre-clé-serper"
doppler secrets set OPENAI_API_KEY "votre-clé-openai"
```

## 🎯 Utilisation avec Doppler

```bash
# Lister les topics configurés
doppler run -- python main.py --list-topics

# Traiter tous les topics
doppler run -- python main.py

# Traiter un topic spécifique  
doppler run -- python main.py --topic "Intelligence Artificielle"

# Mode simulation (sans appels API)
doppler run -- python main.py --dry-run
```

## ⚙️ Configuration

Tout se configure dans `veille.yaml` :

- **Topics** : Nom, mots-clés, chaînes YouTube autorisées
- **Agents** : Rôles, objectifs, contexte
- **Tâches** : Description, agent assigné, format de sortie
- **Paramètres** : Langue, répertoires, planification

## 📊 Résultats

Les synthèses sont générées dans le dossier `syntheses/` :
- Format : `synthese_[Topic]_[Date].md`
- Structure : Résumé, Actualités, Vidéos, Insights, À surveiller

## 🎭 Agents

1. **Researcher** : Recherche d'actualités et vidéos YouTube
2. **Synthesizer** : Rédaction des synthèses markdown

## 🛠️ API Requises (seulement 2 !)

- **Serper API** : Recherche Google ET YouTube en une seule API (https://serper.dev)  
- **OpenAI API** : LLM pour les agents CrewAI (https://platform.openai.com)

**🎉 Plus besoin de YouTube Data API !** Serper gère tout via `site:youtube.com`

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