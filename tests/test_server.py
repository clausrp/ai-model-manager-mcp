"""Tests for the MCP server."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.server import AIModelManagerServer


@pytest.mark.asyncio
async def test_server_initialization():
    """Test server initialization."""
    server = AIModelManagerServer()
    assert server.server is not None
    assert server.config is not None
    assert server.database is not None
    assert isinstance(server.providers, dict)


@pytest.mark.asyncio
async def test_list_models_tool():
    """Test list_models tool."""
    server = AIModelManagerServer()
    
    # Mock provider
    mock_provider = AsyncMock()
    mock_provider.list_models.return_value = []
    server.providers["test"] = mock_provider
    
    result = await server._handle_list_models({})
    assert result is not None
    assert len(result) > 0


@pytest.mark.asyncio
async def test_health_check_tool():
    """Test health_check tool."""
    server = AIModelManagerServer()
    
    # Mock provider
    mock_provider = AsyncMock()
    mock_provider.health_check.return_value = {
        "status": "healthy",
        "available": True,
    }
    server.providers["test"] = mock_provider
    
    result = await server._handle_health_check({})
    assert result is not None
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_tool():
    """Test generate tool."""
    server = AIModelManagerServer()
    
    # Mock provider and response
    from src.models.base import GenerationResponse
    
    mock_response = GenerationResponse(
        model="test-model",
        content="Test response",
        provider="test",
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        cost=0.001,
        latency_ms=100.0,
    )
    
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = mock_response
    server.providers["test"] = mock_provider
    
    result = await server._handle_generate({
        "model": "test-model",
        "provider": "test",
        "prompt": "Test prompt",
    })
    
    assert result is not None
    assert len(result) > 0
    assert "Test response" in result[0].text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
