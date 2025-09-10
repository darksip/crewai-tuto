"""
TUTORIEL CREWAI - Classe CrewAI moderne avec decorators pour la veille automatisée

Ce fichier illustre l'usage moderne de CrewAI 2025 avec les decorators standards.
Il montre comment structurer une équipe d'agents IA pour l'analyse d'actualités.
"""

# Imports CrewAI - Framework d'orchestration d'agents IA
from crewai import Agent, Crew, Task, Process

# Decorators modernes CrewAI 2025 - permettent l'auto-découverte des composants
from crewai.project import CrewBase, agent, task, crew, tool

# Outils pré-construits pour recherche web
from crewai_tools import SerperDevTool

# Module custom pour traitement YouTube
from youtube_processor import collect_videos_for_topic


# TUTORIEL: @CrewBase est le decorator principal qui marque une classe comme "équipe d'agents"
# Il active l'auto-découverte : tous les @agent/@task/@tool sont automatiquement collectés
@CrewBase
class VeilleCrew:
    """
    TUTORIEL: Équipe d'agents IA spécialisée dans la veille technologique

    Cette classe illustre l'architecture moderne CrewAI avec :
    - Séparation configuration/code (YAML externes)
    - Decorators pour auto-découverte des composants
    - Agents spécialisés avec rôles distincts
    - Pipeline de tâches séquentielles
    """

    # TUTORIEL: Liens vers fichiers YAML externes
    # CrewAI charge automatiquement ces configurations au runtime
    agents_config = (
        "config/agents.yaml"  # Définitions des agents (role, goal, backstory)
    )
    tasks_config = (
        "config/tasks.yaml"  # Définitions des tâches (description, expected_output)
    )

    def __init__(self, topic_config=None, videos_context="", pub_date=None):
        """
        TUTORIEL: Initialisation de l'équipe d'agents

        Cette méthode prépare le contexte pour que les agents puissent travailler
        sur un topic spécifique avec les vidéos YouTube déjà collectées.
        """
        # Contexte métier pour cette exécution
        self.topic_config = topic_config or {}  # Topic à traiter (IA, Crypto, etc.)
        self.videos_context = videos_context  # Vidéos YouTube déjà trouvées
        self.pub_date = pub_date  # Date de publication (pour daily/)

        # TUTORIEL: Préparer les variables qui seront injectées dans les tâches
        # Les descriptions des tâches utilisent {topic_name}, {keywords}, etc.
        self.variables = self._prepare_task_variables()

    def _prepare_task_variables(self):
        """
        TUTORIEL: Préparation des variables pour injection dans les tâches

        CrewAI permet d'utiliser des placeholders dans les descriptions YAML.
        Cette fonction prépare toutes les variables nécessaires pour les remplacer.
        """
        if not self.topic_config:
            return {}

        from datetime import datetime

        # Utiliser la date de publication ou aujourd'hui
        target_date = self.pub_date if self.pub_date else datetime.now().date()

        # TUTORIEL: Ces variables seront disponibles dans tasks.yaml via {topic_name}, etc.
        return {
            "topic_name": self.topic_config.get(
                "name", ""
            ),  # Ex: "Intelligence Artificielle"
            "keywords": ", ".join(
                self.topic_config.get("keywords", [])
            ),  # Ex: "IA, LLM, ChatGPT"
            "youtube_channels": ", ".join(
                self.topic_config.get("youtube_channels", [])
            ),
            "volume": self.topic_config.get(
                "volume", 10
            ),  # Nombre de résultats souhaités
            "date": target_date.strftime("%d/%m/%Y"),  # Date formatée française
            "videos_context": self.videos_context,  # Contexte vidéos pré-récupéré
        }

    # TUTORIEL: @tool decorator - Définit un outil utilisable par les agents
    # Les agents peuvent utiliser ces outils pour effectuer des actions concrètes
    @tool
    def serper_search(self):
        """
        TUTORIEL: Outil de recherche web via Serper API

        Cet outil permet aux agents de rechercher des articles sur Google.
        SerperDevTool est un outil pré-construit fourni par crewai-tools.
        """
        return SerperDevTool()

    # TUTORIEL: Exemple d'outil custom - Vous pouvez créer vos propres outils
    @tool
    def youtube_rss_tool(self):
        """
        TUTORIEL: Outil custom pour YouTube RSS

        Cet exemple montre comment créer un outil personnalisé en héritant de BaseTool.
        L'agent peut l'utiliser pour collecter des vidéos YouTube récentes.
        """
        from crewai.tools import BaseTool

        class YouTubeRSSTool(BaseTool):
            name: str = "YouTube RSS Collector"
            description: str = "Collecte les vidéos YouTube récentes via RSS feeds"

            def _run(self, topic_name: str) -> str:
                """
                TUTORIEL: Méthode _run - Point d'entrée de l'outil

                Cette méthode est appelée quand l'agent utilise l'outil.
                Elle doit retourner une chaîne de caractères avec le résultat.
                """
                if hasattr(self, "_topic_config") and self._topic_config:
                    videos = collect_videos_for_topic(self._topic_config)
                    if videos:
                        result = f"Vidéos YouTube récentes pour {topic_name}:\n"
                        for video in videos[:5]:
                            result += f"- {video['title']} ({video['channel']})\n"
                        return result
                return f"Aucune vidéo récente trouvée pour {topic_name}"

        return YouTubeRSSTool()

    # TUTORIEL: @agent decorator - Définit un agent membre de l'équipe
    # Chaque agent a un rôle spécialisé et des outils spécifiques
    @agent
    def researcher(self) -> Agent:
        """
        TUTORIEL: Agent de recherche - Premier membre de l'équipe

        Cet agent est spécialisé dans la recherche d'actualités.
        Il utilise l'outil Serper pour trouver des articles récents.
        Sa configuration (role, goal, backstory) vient de agents.yaml.
        """
        return Agent(
            config=self.agents_config["researcher"],  # Configuration depuis agents.yaml
            tools=[self.serper_search()],  # Outils disponibles pour cet agent
            verbose=True,  # Affichage des détails d'exécution
        )

    # TUTORIEL: Deuxième agent avec un rôle différent
    @agent
    def synthesizer(self) -> Agent:
        """
        TUTORIEL: Agent de synthèse - Deuxième membre de l'équipe

        Cet agent se spécialise dans la rédaction de synthèses.
        Il n'a pas besoin d'outils de recherche, il travaille sur les données
        collectées par l'agent researcher.
        """
        return Agent(
            config=self.agents_config[
                "synthesizer"
            ],  # Configuration depuis agents.yaml
            verbose=True,  # Pas d'outils - utilise les résultats du researcher
        )

    # TUTORIEL: @task decorator - Définit une tâche à accomplir
    # Les tâches sont assignées à un agent et définissent le travail à effectuer
    @task
    def search_articles(self) -> Task:
        """
        TUTORIEL: Première tâche - Recherche d'articles

        Cette tâche demande à l'agent researcher de chercher des actualités.
        La description vient de tasks.yaml et est formatée avec les variables du topic.
        """
        task_config = self.tasks_config[
            "search_articles"
        ].copy()  # Configuration depuis tasks.yaml

        # TUTORIEL: Injection de variables dans la description
        # Remplace {topic_name}, {keywords}, etc. par les vraies valeurs
        if self.variables:
            task_config["description"] = task_config["description"].format(
                **self.variables
            )

        return Task(
            config=task_config,  # Description et expected_output depuis YAML
            agent=self.researcher(),  # Agent assigné à cette tâche
        )

    # TUTORIEL: Deuxième tâche - dépend du résultat de la première
    @task
    def synthesize(self) -> Task:
        """
        TUTORIEL: Tâche de synthèse - Utilise les résultats de la recherche

        Cette tâche prend les articles trouvés par le researcher et les vidéos YouTube
        pré-collectées pour créer une synthèse complète en markdown.
        """
        task_config = self.tasks_config[
            "synthesize"
        ].copy()  # Configuration depuis tasks.yaml

        # TUTORIEL: Formatage dynamique avec contexte vidéos
        if self.variables:
            description = task_config["description"].format(**self.variables)

            # TUTORIEL: Ajout du contexte vidéos YouTube directement dans la description
            # Les vidéos ont été pré-collectées par youtube_processor
            if self.videos_context:
                description += self.videos_context

            task_config["description"] = description

        return Task(
            config=task_config,  # Description enrichie + expected_output
            agent=self.synthesizer(),  # Agent spécialisé en rédaction
        )

    # TUTORIEL: @crew decorator - Assemble l'équipe finale
    # Ce decorator crée l'orchestrateur qui coordonne agents et tâches
    @crew
    def crew(self) -> Crew:
        """
        TUTORIEL: Assemblage de l'équipe complète

        Le @crew decorator rassemble tous les @agent et @task définis dans la classe.
        CrewAI découvre automatiquement ces composants grâce aux decorators.

        Process.sequential = les tâches s'exécutent dans l'ordre (search puis synthesize)
        """
        return Crew(
            agents=self.agents,  # TUTORIEL: Auto-collecté par @CrewBase (researcher, synthesizer)
            tasks=self.tasks,  # TUTORIEL: Auto-collecté par @CrewBase (search_articles, synthesize)
            process=Process.sequential,  # TUTORIEL: Exécution séquentielle des tâches
            verbose=True,  # TUTORIEL: Affichage détaillé du processus
        )

    # TUTORIEL: Méthodes d'utilisation - Comment lancer l'équipe
    def kickoff_for_topic(self, topic_config, videos_context="", pub_date=None):
        """
        TUTORIEL: Lancer l'analyse pour un topic spécifique

        Cette méthode configure le contexte et démarre l'équipe d'agents.
        C'est le point d'entrée principal pour traiter un sujet de veille.
        """
        # TUTORIEL: Mise à jour du contexte dynamique
        self.topic_config = topic_config  # Topic à analyser (IA, Crypto, etc.)
        self.videos_context = videos_context  # Vidéos YouTube déjà collectées
        self.pub_date = pub_date  # Date pour organization daily/
        self.variables = self._prepare_task_variables()  # Re-calcul des variables

        # TUTORIEL: Démarrage de l'équipe - kickoff() lance l'exécution
        return self.crew().kickoff()

    @classmethod
    def create_for_topic(cls, topic_config, videos_context="", pub_date=None):
        """
        TUTORIEL: Factory method - Pattern de création d'instance

        Cette méthode permet de créer une instance pré-configurée de VeilleCrew.
        C'est une alternative propre au constructeur direct.
        """
        instance = cls(topic_config, videos_context, pub_date)
        return instance
