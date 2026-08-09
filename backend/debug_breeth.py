import asyncio
import json
from loguru import logger
from core.breeth_client import BreethMemoryClient

async def test():
    c = BreethMemoryClient()
    res = await c.client.retrieve(query="integration testing", group_id="candidate_test_candidate_hackathon")
    print(json.dumps(res.model_dump(), indent=2))

if __name__ == "__main__":
    asyncio.run(test())
