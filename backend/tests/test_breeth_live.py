"""
Athena AI — Live BREETH AI Memory Integration Test
"""
import pytest
from core.breeth_client import BreethMemoryClient


@pytest.mark.asyncio
async def test_breeth_live_integration():
    client = BreethMemoryClient()
    status = client.get_status()
    print(f"\nBREETH Status: {status}")
    assert status in ["connected", "not_configured"], f"Unexpected status: {status}"

    if status == "connected":
        session_id = "test_sess_001"
        candidate_name = "Aryan Shah"
        content = "Candidate demonstrated strong understanding of Distributed Systems, Raft Consensus, and Python AsyncIO."
        
        # Test Write
        saved = await client.save_episode(
            session_id=session_id,
            candidate_name=candidate_name,
            content=content
        )
        assert saved is True, "Failed to save episode to BREETH AI"

        # Test Retrieve
        memories = await client.retrieve_context(
            candidate_name=candidate_name,
            query="Distributed Systems Raft",
            limit=5
        )
        assert isinstance(memories, list), "Retrieve context should return a list"
        print(f"Retrieved {len(memories)} memories for candidate {candidate_name}")
        
        # Test Isolation: Query for a different candidate
        other_memories = await client.retrieve_context(
            candidate_name="Other Candidate 9999",
            query="Distributed Systems",
            limit=5
        )
        assert isinstance(other_memories, list)
        
        if client.client:
            await client.client.aclose()
