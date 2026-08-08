"""
Athena AI — Provider Architecture Test
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import ProviderFactory, OpenAICompatibleProvider, BreathAILayerProvider
from core.config import settings

async def test_providers():
    print("✅ Testing Provider Factory...")

    # Default should be OpenAI Compatible
    primary = ProviderFactory.get_primary()
    assert isinstance(primary, OpenAICompatibleProvider)
    print("   Primary Provider loaded successfully ✓")

    # If Breath AI keys are missing, breath provider should fallback to primary
    settings.BREATH_API_KEY = ""
    breath_fallback = ProviderFactory.get_breath_layer()
    assert isinstance(breath_fallback, OpenAICompatibleProvider)
    print("   Breath AI correctly falls back to Primary when unconfigured ✓")

    # If configured, it should return the Breath AI provider
    settings.BREATH_API_KEY = "mock_key"
    # reset singleton
    ProviderFactory._breath_provider = None
    
    breath_active = ProviderFactory.get_breath_layer()
    assert isinstance(breath_active, BreathAILayerProvider)
    print("   Breath AI activates when configured ✓")

    print("\n✅ All provider tests passed!")


if __name__ == "__main__":
    asyncio.run(test_providers())
