"""
Athena AI — Basic Backend Test
Tests the interview flow without external dependencies
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.interview import (
    StartInterviewRequest, RespondRequest,
    QuestionType, DifficultyLevel
)


async def test_models():
    """Test that Pydantic models serialize correctly."""
    print("✅ Testing Pydantic models...")

    req = StartInterviewRequest(
        name="Test Candidate",
        completed_missions=[1, 2, 3],
        skipped_topics=["Quantization"],
        learning_signals={"RAG": 0.8, "Embeddings": 0.4},
    )
    assert req.name == "Test Candidate"
    assert req.completed_missions == [1, 2, 3]
    print(f"   StartInterviewRequest: {req.name} ✓")

    respond = RespondRequest(
        session_id="sess_test123",
        answer="RAG works by retrieving relevant chunks from a vector database.",
    )
    assert respond.session_id == "sess_test123"
    print(f"   RespondRequest: {respond.session_id} ✓")

    print("✅ All model tests passed!")


async def test_knowledge_graph():
    """Test the knowledge graph."""
    print("\n✅ Testing Knowledge Graph...")
    from knowledge.knowledge_graph import KnowledgeGraph

    graph = KnowledgeGraph()
    print(f"   Nodes: {graph.graph.number_of_nodes()} ✓")
    print(f"   Edges: {graph.graph.number_of_edges()} ✓")

    # Test confidence update
    graph.update_confidence("RAG", 0.8)
    assert graph.graph.nodes["RAG"]["confidence"] > 0.5
    print("   Confidence update: ✓")

    # Test weakest node
    weakest = graph.get_weakest_untested_node([])
    assert weakest is not None
    print(f"   Weakest untested node: {weakest} ✓")

    # Test scores
    scores = graph.get_all_scores()
    assert len(scores) > 0
    print(f"   All scores: {len(scores)} topics ✓")

    # Test serialization
    data = graph.to_dict()
    assert "nodes" in data and "edges" in data
    print("   Serialization: ✓")

    print("✅ Knowledge Graph tests passed!")


async def test_memory():
    """Test the memory engine."""
    print("\n✅ Testing Memory Engine...")
    from memory.memory_engine import MemoryEngine

    mem = MemoryEngine()

    # Add Q&A
    mem.record_qa(
        question="What is RAG?",
        answer="Retrieval Augmented Generation...",
        topic="RAG",
        curriculum_day=3,
        question_type="theory",
        score=0.8,
    )

    recent = mem.short_term.get_recent(3)
    assert len(recent) == 1
    print(f"   Short-term memory: {len(recent)} entry ✓")

    context = mem.get_context_for_llm()
    assert "RAG" in context
    print("   LLM context: ✓")

    summary = mem.interview.get_summary()
    assert "RAG" in summary["topics_covered"]
    assert 3 in summary["days_covered"]
    print(f"   Interview memory: {summary} ✓")

    print("✅ Memory Engine tests passed!")


async def main():
    print("=" * 50)
    print("🦉 Athena AI — Backend Unit Tests")
    print("=" * 50)

    await test_models()
    await test_knowledge_graph()
    await test_memory()

    print("\n" + "=" * 50)
    print("✅ All tests passed! Backend is healthy.")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
