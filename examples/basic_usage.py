"""
Basic usage examples for the AI Model Manager MCP Server.

This file demonstrates how to interact with the server programmatically.
Note: The server is designed to be used via MCP protocol, but these examples
show the underlying functionality.
"""

import asyncio
from src.server import AIModelManagerServer
from src.models.base import GenerationRequest


async def example_list_models():
    """Example: List all available models."""
    print("\n=== Listing All Models ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_list_models({})
    print(result[0].text)


async def example_list_models_by_provider():
    """Example: List models from a specific provider."""
    print("\n=== Listing Ollama Models ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_list_models({"provider": "ollama"})
    print(result[0].text)


async def example_get_model_info():
    """Example: Get information about a specific model."""
    print("\n=== Getting Model Info ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_get_model_info({
        "model": "llama3.2",
        "provider": "ollama"
    })
    print(result[0].text)


async def example_generate_text():
    """Example: Generate text with a model."""
    print("\n=== Generating Text ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_generate({
        "model": "llama3.2",
        "provider": "ollama",
        "prompt": "Explain what an MCP server is in one sentence.",
        "temperature": 0.7,
        "max_tokens": 100
    })
    print(result[0].text)


async def example_compare_models():
    """Example: Compare outputs from multiple models."""
    print("\n=== Comparing Models ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_compare_models({
        "models": [
            {"model": "llama3.2", "provider": "ollama"},
            {"model": "mistral", "provider": "ollama"},
        ],
        "prompt": "Write a haiku about artificial intelligence.",
        "temperature": 0.8
    })
    print(result[0].text)


async def example_usage_stats():
    """Example: Get usage statistics."""
    print("\n=== Usage Statistics ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_get_usage_stats({"group_by": "provider"})
    print(result[0].text)


async def example_health_check():
    """Example: Check provider health."""
    print("\n=== Health Check ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_health_check({})
    print(result[0].text)


async def example_save_conversation():
    """Example: Save a conversation."""
    print("\n=== Saving Conversation ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_save_conversation({
        "title": "Example Conversation",
        "model": "llama3.2",
        "provider": "ollama",
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi! How can I help you?"},
            {"role": "user", "content": "Tell me about MCP servers."},
            {"role": "assistant", "content": "MCP servers provide..."}
        ]
    })
    print(result[0].text)


async def example_list_conversations():
    """Example: List saved conversations."""
    print("\n=== Listing Conversations ===")
    server = AIModelManagerServer()
    await server.initialize()
    
    result = await server._handle_list_conversations({"limit": 10})
    print(result[0].text)


async def run_all_examples():
    """Run all examples."""
    print("=" * 60)
    print("AI Model Manager MCP Server - Usage Examples")
    print("=" * 60)
    
    try:
        # Basic examples
        await example_list_models()
        await example_list_models_by_provider()
        await example_get_model_info()
        
        # Generation examples
        await example_generate_text()
        await example_compare_models()
        
        # Management examples
        await example_usage_stats()
        await example_health_check()
        await example_save_conversation()
        await example_list_conversations()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nNote: Make sure you have:")
        print("1. Ollama installed and running")
        print("2. At least one model pulled (e.g., 'ollama pull llama3.2')")
        print("3. Configured your .env file with API keys (if using cloud providers)")


if __name__ == "__main__":
    asyncio.run(run_all_examples())

# Made with Bob
