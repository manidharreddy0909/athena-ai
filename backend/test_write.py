import asyncio
import os
from loguru import logger
from core.breeth_client import BreethMemoryClient

async def test_breeth():
    logger.info("Initializing BreethMemoryClient...")
    client = BreethMemoryClient()
    
    if not client.is_configured:
        logger.error("BREETH_API_KEY is missing or SDK is not installed. Test failed.")
        return
        
    candidate_name = "test_candidate_hackathon"
    test_memory = "This is a mandatory test memory injected during integration testing."
    
    # 1. Test Write
    logger.info(f"Writing test episode for candidate: {candidate_name}...")
    success = await client.save_episode(
        session_id="test_session_123",
        candidate_name=candidate_name,
        content=test_memory
    )
    
    if success:
        logger.info("✅ Write succeeded!")
    else:
        logger.error("❌ Write failed!")
        return
        
    # Wait a moment for indexing
    await asyncio.sleep(2)
    
    # 2. Test Retrieval
    logger.info(f"Retrieving context for candidate: {candidate_name}...")
    results = await client.retrieve_context(
        candidate_name=candidate_name,
        query="test memory",
        limit=3
    )
    
    if results:
        logger.info(f"✅ Retrieval succeeded! Found {len(results)} memories.")
        for idx, mem in enumerate(results):
            logger.info(f"Memory {idx+1}: {mem}")
            
        # 3. Verify match
        if any(test_memory in mem for mem in results):
            logger.info("✅ Verification passed: Retrieved data matches the test data.")
        else:
            logger.error("❌ Verification failed: Test data not found in results.")
    else:
        logger.error("❌ Retrieval failed or returned no results.")

if __name__ == "__main__":
    asyncio.run(test_breeth())
