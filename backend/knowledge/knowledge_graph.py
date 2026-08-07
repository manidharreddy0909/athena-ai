"""
Athena AI — Knowledge Graph Engine
Directed dependency graph of curriculum topics
"""
import networkx as nx
from typing import Optional
from loguru import logger


# ─────────────────────────────────────────────
# Curriculum Knowledge Graph Definition
# ─────────────────────────────────────────────

CURRICULUM_GRAPH_DATA = {
    "nodes": [
        {"id": "Prompt Engineering",  "day": 1,  "category": "foundations"},
        {"id": "RAG",                  "day": 3,  "category": "retrieval"},
        {"id": "Embeddings",           "day": 4,  "category": "retrieval"},
        {"id": "Chunking",             "day": 5,  "category": "retrieval"},
        {"id": "Vector Database",      "day": 6,  "category": "retrieval"},
        {"id": "Retriever",            "day": 7,  "category": "retrieval"},
        {"id": "Reranker",             "day": 8,  "category": "retrieval"},
        {"id": "Evaluation",           "day": 10, "category": "quality"},
        {"id": "Agentic AI",           "day": 12, "category": "agents"},
        {"id": "MCP",                  "day": 15, "category": "agents"},
        {"id": "LangGraph",            "day": 16, "category": "agents"},
        {"id": "AI Deployment",        "day": 20, "category": "production"},
        {"id": "Production AI",        "day": 25, "category": "production"},
        {"id": "Vector DB Advanced",   "day": 9,  "category": "retrieval"},
        {"id": "GraphRAG",             "day": 11, "category": "retrieval"},
        {"id": "Fine-Tuning",          "day": 18, "category": "training"},
        {"id": "Monitoring",           "day": 22, "category": "production"},
    ],
    "edges": [
        # Core RAG pipeline
        ("Prompt Engineering", "RAG",           {"strength": 0.8, "type": "prerequisite"}),
        ("Embeddings",         "RAG",           {"strength": 0.95, "type": "prerequisite"}),
        ("Chunking",           "Embeddings",    {"strength": 0.9,  "type": "prerequisite"}),
        ("Chunking",           "RAG",           {"strength": 0.85, "type": "prerequisite"}),
        ("Vector Database",    "RAG",           {"strength": 0.95, "type": "prerequisite"}),
        ("Retriever",          "RAG",           {"strength": 0.9,  "type": "component"}),
        ("Reranker",           "Retriever",     {"strength": 0.8,  "type": "enhancement"}),
        ("Vector Database",    "Retriever",     {"strength": 0.85, "type": "prerequisite"}),
        ("Embeddings",         "Vector Database",{"strength": 0.95, "type": "prerequisite"}),
        # Advanced retrieval
        ("RAG",                "GraphRAG",      {"strength": 0.8,  "type": "advanced"}),
        ("Vector Database",    "Vector DB Advanced", {"strength": 0.7, "type": "advanced"}),
        ("GraphRAG",           "Vector DB Advanced", {"strength": 0.75, "type": "related"}),
        # Evaluation
        ("RAG",                "Evaluation",    {"strength": 0.75, "type": "related"}),
        ("Prompt Engineering", "Evaluation",    {"strength": 0.7,  "type": "related"}),
        # Agents
        ("RAG",                "Agentic AI",    {"strength": 0.8,  "type": "prerequisite"}),
        ("Agentic AI",         "MCP",           {"strength": 0.85, "type": "component"}),
        ("Agentic AI",         "LangGraph",     {"strength": 0.9,  "type": "implementation"}),
        ("MCP",                "LangGraph",     {"strength": 0.7,  "type": "related"}),
        # Production
        ("Agentic AI",         "AI Deployment", {"strength": 0.8,  "type": "prerequisite"}),
        ("AI Deployment",      "Production AI", {"strength": 0.9,  "type": "prerequisite"}),
        ("Production AI",      "Monitoring",    {"strength": 0.85, "type": "component"}),
        # Fine-tuning
        ("Embeddings",         "Fine-Tuning",   {"strength": 0.6,  "type": "related"}),
        ("Fine-Tuning",        "Production AI", {"strength": 0.7,  "type": "related"}),
    ]
}


class KnowledgeGraph:
    """
    Directed dependency graph of AI curriculum topics.
    Nodes carry confidence scores. Weak nodes trigger targeted questions.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self):
        """Build the graph from the curriculum definition."""
        for node_data in CURRICULUM_GRAPH_DATA["nodes"]:
            self.graph.add_node(
                node_data["id"],
                day=node_data["day"],
                category=node_data["category"],
                confidence=0.5,  # neutral starting confidence
                question_count=0,
                last_asked=None,
            )
        for src, dst, attrs in CURRICULUM_GRAPH_DATA["edges"]:
            self.graph.add_edge(src, dst, **attrs)
        logger.info(f"📊 Knowledge Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def update_confidence(self, topic: str, score: float, alpha: float = 0.3):
        """Exponential moving average update for topic confidence."""
        if topic in self.graph.nodes:
            current = self.graph.nodes[topic]["confidence"]
            new_confidence = (1 - alpha) * current + alpha * score
            self.graph.nodes[topic]["confidence"] = round(new_confidence, 3)
            self.graph.nodes[topic]["question_count"] += 1

    def get_weakest_untested_node(self, tested_topics: list[str], threshold: float = 0.75) -> Optional[str]:
        """
        Find the weakest node that:
        1. Has not been adequately tested yet
        2. Has all prerequisites above threshold OR no prerequisites
        Returns None if all topics are well-covered.
        """
        candidates = []
        for node in self.graph.nodes:
            if self.graph.nodes[node]["confidence"] >= threshold:
                continue  # already strong
            # Check prerequisites are covered
            prereqs = list(self.graph.predecessors(node))
            prereqs_ok = all(
                self.graph.nodes[p]["confidence"] >= 0.5 for p in prereqs
            )
            if prereqs_ok:
                candidates.append((node, self.graph.nodes[node]["confidence"]))

        if not candidates:
            return None
        # Return node with lowest confidence
        return min(candidates, key=lambda x: x[1])[0]

    def get_dependency_path(self, topic: str) -> list[str]:
        """Get the dependency chain for a topic (what it depends on)."""
        if topic not in self.graph.nodes:
            return [topic]
        predecessors = list(nx.ancestors(self.graph, topic))
        path = [topic] + predecessors[:4]  # limit to top 4
        return path

    def get_curriculum_day(self, topic: str) -> Optional[int]:
        """Get the curriculum day for a topic."""
        if topic in self.graph.nodes:
            return self.graph.nodes[topic].get("day")
        return None

    def get_all_scores(self) -> dict[str, float]:
        """Get confidence scores for all nodes."""
        return {
            node: self.graph.nodes[node]["confidence"]
            for node in self.graph.nodes
        }

    def get_topics_for_day(self, day: int) -> list[str]:
        """Get all topics belonging to a specific curriculum day."""
        return [
            node for node in self.graph.nodes
            if self.graph.nodes[node].get("day") == day
        ]

    def to_dict(self) -> dict:
        """Serialize graph for API responses and frontend visualization."""
        return {
            "nodes": [
                {
                    "id": node,
                    "day": self.graph.nodes[node]["day"],
                    "category": self.graph.nodes[node]["category"],
                    "confidence": self.graph.nodes[node]["confidence"],
                }
                for node in self.graph.nodes
            ],
            "edges": [
                {
                    "source": src,
                    "target": dst,
                    "strength": data.get("strength", 0.5),
                    "type": data.get("type", "related"),
                }
                for src, dst, data in self.graph.edges(data=True)
            ],
        }
