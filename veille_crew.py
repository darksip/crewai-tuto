"""
Classe CrewAI moderne avec decorators pour la veille automatisée
"""
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, tool
from crewai_tools import SerperDevTool
from youtube_processor import collect_videos_for_topic


@CrewBase
class VeilleCrew:
    """Crew de veille automatisée avec annotations modernes CrewAI"""

    # Chemins vers les configurations YAML
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, topic_config=None, videos_context="", pub_date=None):
        """Initialiser avec le contexte du topic et des vidéos"""
        self.topic_config = topic_config or {}
        self.videos_context = videos_context
        self.pub_date = pub_date
        
        # Variables pour le formatage des tâches
        self.variables = self._prepare_task_variables()
    
    def _prepare_task_variables(self):
        """Préparer les variables pour le formatage des tâches"""
        if not self.topic_config:
            return {}
            
        from datetime import datetime
        target_date = self.pub_date if self.pub_date else datetime.now().date()
        
        return {
            "topic_name": self.topic_config.get("name", ""),
            "keywords": ", ".join(self.topic_config.get("keywords", [])),
            "youtube_channels": ", ".join(self.topic_config.get("youtube_channels", [])),
            "volume": self.topic_config.get("volume", 10),
            "date": target_date.strftime("%d/%m/%Y"),
            "videos_context": self.videos_context,
        }

    @tool
    def serper_search(self):
        """Outil de recherche Serper pour articles"""
        return SerperDevTool()
    
    @tool
    def youtube_rss_tool(self):
        """Outil custom pour récupérer des vidéos YouTube via RSS"""
        from crewai.tools import BaseTool
        
        class YouTubeRSSTool(BaseTool):
            name: str = "YouTube RSS Collector"
            description: str = "Collecte les vidéos YouTube récentes via RSS feeds"
            
            def _run(self, topic_name: str) -> str:
                """Collecter les vidéos pour un topic"""
                if hasattr(self, '_topic_config') and self._topic_config:
                    videos = collect_videos_for_topic(self._topic_config)
                    if videos:
                        result = f"Vidéos YouTube récentes pour {topic_name}:\n"
                        for video in videos[:5]:
                            result += f"- {video['title']} ({video['channel']})\n"
                        return result
                return f"Aucune vidéo récente trouvée pour {topic_name}"
        
        return YouTubeRSSTool()

    @agent
    def researcher(self) -> Agent:
        """Agent de recherche d'actualités"""
        return Agent(
            config=self.agents_config['researcher'],
            tools=[self.serper_search()],
            verbose=True
        )

    @agent
    def synthesizer(self) -> Agent:
        """Agent de rédaction de synthèses"""
        return Agent(
            config=self.agents_config['synthesizer'],
            verbose=True
        )

    @task
    def search_articles(self) -> Task:
        """Tâche de recherche d'articles"""
        task_config = self.tasks_config['search_articles'].copy()
        
        # Formater la description avec les variables du topic
        if self.variables:
            task_config['description'] = task_config['description'].format(**self.variables)
        
        return Task(
            config=task_config,
            agent=self.researcher()
        )

    @task
    def synthesize(self) -> Task:
        """Tâche de synthèse finale"""
        task_config = self.tasks_config['synthesize'].copy()
        
        # Formater la description avec les variables du topic
        if self.variables:
            description = task_config['description'].format(**self.variables)
            
            # Ajouter le contexte vidéos si disponible
            if self.videos_context:
                description += self.videos_context
            
            task_config['description'] = description
        
        return Task(
            config=task_config,
            agent=self.synthesizer()
        )

    @crew
    def crew(self) -> Crew:
        """Crew principal pour la veille"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )

    def kickoff_for_topic(self, topic_config, videos_context="", pub_date=None):
        """Lancer la veille pour un topic spécifique avec contexte"""
        # Mettre à jour le contexte
        self.topic_config = topic_config
        self.videos_context = videos_context
        self.pub_date = pub_date
        self.variables = self._prepare_task_variables()
        
        # Lancer le crew
        return self.crew().kickoff()

    @classmethod
    def create_for_topic(cls, topic_config, videos_context="", pub_date=None):
        """Factory method pour créer une instance configurée"""
        instance = cls(topic_config, videos_context, pub_date)
        return instance