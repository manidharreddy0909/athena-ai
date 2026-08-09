"""
Athena AI — Provider Architecture Test
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import ProviderFactory, OpenAICompatibleProvider, BreethAILayerProvider
from core.config import settings

async def test_providers():
    print("✅ Testing Provider Factory...")

    # Default should be OpenAI Compatible
    primary = ProviderFactory.get_primary()
    assert isinstance(primary, OpenAICompatibleProvider)
    print("   Primary Provider loaded successfully ✓")

    # If Breeth AI keys are missing, breeth provider should fallback to primary
    settings.BREETH_API_KEY = ""
    breeth_fallback = ProviderFactory.get_breeth_layer()
    assert isinstance(breeth_fallback, OpenAICompatibleProvider)
    print("   BREETH AI correctly falls back to Primary when unconfigured ✓")

    # If configured, it should return the Breeth AI provider
    settings.BREETH_API_KEY = "mock_key"
    # reset singleton
    ProviderFactory._breeth_provider = None
    
    breeth_active = ProviderFactory.get_breeth_layer()
    assert isinstance(breeth_active, BreethAILayerProvider)
    print("   BREETH AI activates when configured ✓")

    print("\n✅ All provider tests passed!")


if __name__ == "__main__":
    asyncio.run(test_providers())
