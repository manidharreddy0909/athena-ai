"""
Athena AI — Universal Domain Engine (Phase 6)
Enables Athena to conduct expert interviews in ANY technical domain,
not just AI/ML. Domains are discovered dynamically via LLM or pre-loaded
from structured YAML/JSON configs.
"""
from typing import Dict, List, Optional, Any
from loguru import logger
from enum import Enum
import json
from core.llm import chat_completion


class InterviewDomain(str, Enum):
    """Supported interview domains."""
    AI_ML = "ai_ml"
    SOFTWARE_ENGINEERING = "software_engineering"
    DATA_ENGINEERING = "data_engineering"
    CLOUD_DEVOPS = "cloud_devops"
    FRONTEND = "frontend"
    BACKEND = "backend"
    PRODUCT_MANAGEMENT = "product_management"
    SECURITY = "security"
    CUSTOM = "custom"


# Pre-defined domain knowledge graphs (topic -> day, category, dependencies)
DOMAIN_CONFIGS: Dict[str, Dict[str, Any]] = {
    "ai_ml": {
        "name": "AI / Machine Learning",
        "description": "Covers LLMs, RAG, agents, embeddings, fine-tuning and production AI.",
        "nodes": [
            {"id": "Prompt Engineering",  "day": 1,  "category": "foundations"},
            {"id": "RAG",                 "day": 3,  "category": "retrieval"},
            {"id": "Embeddings",          "day": 4,  "category": "retrieval"},
            {"id": "Vector Database",     "day": 6,  "category": "retrieval"},
            {"id": "Agentic AI",          "day": 12, "category": "agents"},
            {"id": "LangGraph",           "day": 16, "category": "agents"},
            {"id": "Fine-Tuning",         "day": 18, "category": "training"},
            {"id": "Production AI",       "day": 25, "category": "production"},
        ],
        "edges": [
            ("Prompt Engineering", "RAG"),
            ("Embeddings", "RAG"),
            ("Vector Database", "RAG"),
            ("RAG", "Agentic AI"),
            ("Agentic AI", "LangGraph"),
            ("RAG", "Fine-Tuning"),
            ("Fine-Tuning", "Production AI"),
        ],
        "core_competencies": ["RAG", "Embeddings", "Agentic AI", "LLMs"],
    },
    "software_engineering": {
        "name": "Software Engineering",
        "description": "Covers data structures, algorithms, system design, and engineering practices.",
        "nodes": [
            {"id": "Data Structures",     "day": 1,  "category": "fundamentals"},
            {"id": "Algorithms",          "day": 2,  "category": "fundamentals"},
            {"id": "Object-Oriented Design", "day": 3, "category": "design"},
            {"id": "Design Patterns",     "day": 4,  "category": "design"},
            {"id": "System Design",       "day": 5,  "category": "architecture"},
            {"id": "Databases",           "day": 6,  "category": "data"},
            {"id": "Distributed Systems", "day": 7,  "category": "architecture"},
            {"id": "API Design",          "day": 8,  "category": "architecture"},
            {"id": "Testing",             "day": 9,  "category": "quality"},
            {"id": "Performance",         "day": 10, "category": "quality"},
        ],
        "edges": [
            ("Data Structures", "Algorithms"),
            ("Algorithms", "System Design"),
            ("Object-Oriented Design", "Design Patterns"),
            ("Design Patterns", "System Design"),
            ("System Design", "Distributed Systems"),
            ("Databases", "System Design"),
            ("API Design", "System Design"),
            ("Testing", "Performance"),
        ],
        "core_competencies": ["System Design", "Algorithms", "Distributed Systems"],
    },
    "data_engineering": {
        "name": "Data Engineering",
        "description": "Covers pipelines, warehousing, streaming, and data quality.",
        "nodes": [
            {"id": "ETL Fundamentals",    "day": 1,  "category": "pipelines"},
            {"id": "SQL & Databases",     "day": 2,  "category": "storage"},
            {"id": "Data Warehousing",    "day": 3,  "category": "storage"},
            {"id": "Apache Spark",        "day": 4,  "category": "processing"},
            {"id": "Kafka Streaming",     "day": 5,  "category": "streaming"},
            {"id": "dbt",                 "day": 6,  "category": "transformation"},
            {"id": "Airflow",             "day": 7,  "category": "orchestration"},
            {"id": "Data Quality",        "day": 8,  "category": "quality"},
            {"id": "Data Lakehouse",      "day": 9,  "category": "architecture"},
            {"id": "ML Pipelines",        "day": 10, "category": "mlops"},
        ],
        "edges": [
            ("ETL Fundamentals", "Apache Spark"),
            ("SQL & Databases", "Data Warehousing"),
            ("Data Warehousing", "Data Lakehouse"),
            ("Apache Spark", "Kafka Streaming"),
            ("Kafka Streaming", "ML Pipelines"),
            ("dbt", "Data Warehousing"),
            ("Airflow", "ETL Fundamentals"),
            ("Data Quality", "Data Lakehouse"),
        ],
        "core_competencies": ["Apache Spark", "Kafka Streaming", "Data Warehousing"],
    },
    "cloud_devops": {
        "name": "Cloud & DevOps",
        "description": "Covers cloud platforms, CI/CD, containers, and infrastructure as code.",
        "nodes": [
            {"id": "Linux Fundamentals",  "day": 1,  "category": "foundations"},
            {"id": "Docker",              "day": 2,  "category": "containers"},
            {"id": "Kubernetes",          "day": 3,  "category": "containers"},
            {"id": "CI/CD",               "day": 4,  "category": "automation"},
            {"id": "Terraform",           "day": 5,  "category": "iac"},
            {"id": "AWS / GCP / Azure",   "day": 6,  "category": "cloud"},
            {"id": "Monitoring & Logging","day": 7,  "category": "observability"},
            {"id": "Site Reliability",    "day": 8,  "category": "reliability"},
            {"id": "Security (DevSecOps)","day": 9,  "category": "security"},
            {"id": "Microservices",       "day": 10, "category": "architecture"},
        ],
        "edges": [
            ("Linux Fundamentals", "Docker"),
            ("Docker", "Kubernetes"),
            ("Kubernetes", "CI/CD"),
            ("CI/CD", "Terraform"),
            ("Terraform", "AWS / GCP / Azure"),
            ("AWS / GCP / Azure", "Monitoring & Logging"),
            ("Monitoring & Logging", "Site Reliability"),
            ("Kubernetes", "Microservices"),
        ],
        "core_competencies": ["Kubernetes", "CI/CD", "AWS / GCP / Azure"],
    },
}


class DomainEngine:
    """
    Universal Domain Engine.
    Provides domain-specific knowledge graphs, competency maps,
    and prompt context for any interview domain.
    """

    @classmethod
    async def create(cls, domain: InterviewDomain, custom_topic: Optional[str] = None) -> 'DomainEngine':
        if domain == InterviewDomain.CUSTOM and custom_topic:
            try:
                config = await cls.generate_custom_domain(custom_topic)
                return cls(domain, custom_config=config)
            except Exception as e:
                logger.error(f"Failed to generate custom domain config for '{custom_topic}': {e}")
                # Fallback
                return cls(InterviewDomain.AI_ML)
        return cls(domain)

    @classmethod
    async def generate_custom_domain(cls, topic: str) -> Dict[str, Any]:
        """Dynamically generate a Domain Config for a custom topic using LLM."""
        prompt = (
            f"Generate a technical interview curriculum knowledge graph for the topic: '{topic}'.\n"
            "Respond ONLY with a valid JSON object following exactly this schema:\n"
            "{\n"
            "  \"name\": \"Name of the topic\",\n"
            "  \"description\": \"Brief description\",\n"
            "  \"nodes\": [ {\"id\": \"Subtopic 1\", \"day\": 1, \"category\": \"foundations\"}, ... ],\n"
            "  \"edges\": [ [\"Subtopic 1\", \"Subtopic 2\"], ... ],\n"
            "  \"core_competencies\": [\"Subtopic 1\", \"Subtopic 3\"]\n"
            "}\n"
            "Ensure there are at least 6 nodes across various 'days' (1 to 10), and logical directed edges where item 0 is a prerequisite for item 1."
        )
        
        from core.llm import chat_completion, parse_json_response
        response_text = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            json_mode=True
        )
        
        config = parse_json_response(response_text)
        
        # Ensure edges is a list of tuples as expected by __init__
        if "edges" in config and isinstance(config["edges"], list):
            new_edges = []
            for edge in config["edges"]:
                if isinstance(edge, list) and len(edge) == 2:
                    new_edges.append((edge[0], edge[1]))
            config["edges"] = new_edges
            
        return config

    def __init__(self, domain: InterviewDomain = InterviewDomain.AI_ML, custom_config: Optional[Dict] = None):
        self.domain = domain
        if domain == InterviewDomain.CUSTOM and custom_config:
            self.config = custom_config
        elif domain.value in DOMAIN_CONFIGS:
            self.config = DOMAIN_CONFIGS[domain.value]
        else:
            logger.warning(f"Domain '{domain}' not found in registry. Falling back to AI/ML.")
            self.config = DOMAIN_CONFIGS["ai_ml"]

        self.nodes: List[Dict] = self.config.get("nodes", [])
        self.edges: List = self.config.get("edges", [])
        self.core_competencies: List[str] = self.config.get("core_competencies", [])
        logger.info(f"🌐 Domain Engine initialized: {self.config.get('name', domain)}")

    def get_all_topics(self) -> List[str]:
        return [n["id"] for n in self.nodes]

    def get_topics_for_day(self, day: int) -> List[str]:
        return [n["id"] for n in self.nodes if n.get("day") == day]

    def get_topic_day(self, topic: str) -> Optional[int]:
        for n in self.nodes:
            if n["id"] == topic:
                return n.get("day")
        return None

    def get_topic_category(self, topic: str) -> Optional[str]:
        for n in self.nodes:
            if n["id"] == topic:
                return n.get("category")
        return None

    def get_total_days(self) -> int:
        days = [n.get("day", 0) for n in self.nodes]
        return max(days) if days else 0

    def get_initial_topic(self, skipped_topics: List[str]) -> str:
        """Select the first interview topic based on candidate skipped topics or core competencies."""
        all_topics = self.get_all_topics()

        # Start from a skipped topic if it exists (tests their weak area)
        for t in skipped_topics:
            if t in all_topics:
                return t

        # Otherwise start from core competency
        for t in self.core_competencies:
            if t in all_topics:
                return t

        # Fallback: first topic in the graph
        return all_topics[0] if all_topics else "General Knowledge"

    def get_system_prompt_context(self) -> str:
        """Returns a domain-specific context string to prepend to all LLM prompts."""
        return (
            f"You are Athena, an expert interviewer specializing in {self.config.get('name', 'technology')}. "
            f"This interview covers: {self.config.get('description', '')} "
            f"Core competency areas: {', '.join(self.core_competencies)}."
        )


# Default singleton for AI/ML (existing behavior preserved)
default_domain_engine = DomainEngine(InterviewDomain.AI_ML)
