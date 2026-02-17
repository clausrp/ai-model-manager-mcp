"""Main MCP server implementation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .models.base import GenerationRequest, ModelCapability
from .providers import (
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    MistralProvider,
)
from .storage import Database, Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIModelManagerServer:
    """MCP Server for AI Model Management."""

    def __init__(self):
        self.server = Server("ai-model-manager")
        self.config = Config()
        self.database = Database(self.config.get_database_path())
        self.providers: Dict[str, Any] = {}
        
        # Register handlers
        self._register_handlers()

    async def initialize(self) -> None:
        """Initialize the server and providers."""
        # Initialize database
        await self.database.initialize()
        
        # Initialize providers
        await self._initialize_providers()
        
        logger.info("AI Model Manager MCP Server initialized")

    async def _initialize_providers(self) -> None:
        """Initialize all configured providers."""
        # Ollama (local)
        if self.config.is_provider_configured("ollama"):
            try:
                ollama_config = self.config.get_provider_config("ollama")
                self.providers["ollama"] = OllamaProvider(ollama_config)
                logger.info("Ollama provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama: {e}")

        # OpenAI
        if self.config.is_provider_configured("openai"):
            try:
                openai_config = self.config.get_provider_config("openai")
                self.providers["openai"] = OpenAIProvider(openai_config)
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")

        # Anthropic
        if self.config.is_provider_configured("anthropic"):
            try:
                anthropic_config = self.config.get_provider_config("anthropic")
                self.providers["anthropic"] = AnthropicProvider(anthropic_config)
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {e}")

        # Google
        if self.config.is_provider_configured("google"):
            try:
                google_config = self.config.get_provider_config("google")
                self.providers["google"] = GoogleProvider(google_config)
                logger.info("Google provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google: {e}")

        # Mistral
        if self.config.is_provider_configured("mistral"):
            try:
                mistral_config = self.config.get_provider_config("mistral")
                self.providers["mistral"] = MistralProvider(mistral_config)
                logger.info("Mistral provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Mistral: {e}")

    def _register_handlers(self) -> None:
        """Register MCP handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="list_models",
                    description="List all available AI models from all providers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "description": "Filter by provider (ollama, openai, anthropic, google, mistral)",
                            },
                            "capability": {
                                "type": "string",
                                "description": "Filter by capability (chat, completion, vision, function_calling, code)",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_model_info",
                    description="Get detailed information about a specific model",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model": {
                                "type": "string",
                                "description": "Model name",
                            },
                            "provider": {
                                "type": "string",
                                "description": "Provider name",
                            },
                        },
                        "required": ["model", "provider"],
                    },
                ),
                Tool(
                    name="generate",
                    description="Generate text using a specified model",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model": {
                                "type": "string",
                                "description": "Model name",
                            },
                            "provider": {
                                "type": "string",
                                "description": "Provider name",
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Text prompt",
                            },
                            "messages": {
                                "type": "array",
                                "description": "Chat messages",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {"type": "string"},
                                        "content": {"type": "string"},
                                    },
                                },
                            },
                            "system_prompt": {
                                "type": "string",
                                "description": "System prompt",
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum tokens to generate",
                            },
                            "temperature": {
                                "type": "number",
                                "description": "Temperature (0-2)",
                                "default": 0.7,
                            },
                        },
                        "required": ["model", "provider"],
                    },
                ),
                Tool(
                    name="compare_models",
                    description="Compare outputs from multiple models for the same prompt",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "models": {
                                "type": "array",
                                "description": "List of model/provider pairs",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "model": {"type": "string"},
                                        "provider": {"type": "string"},
                                    },
                                },
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Text prompt",
                            },
                            "temperature": {
                                "type": "number",
                                "default": 0.7,
                            },
                        },
                        "required": ["models", "prompt"],
                    },
                ),
                Tool(
                    name="get_usage_stats",
                    description="Get usage statistics and costs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model": {
                                "type": "string",
                                "description": "Filter by model",
                            },
                            "provider": {
                                "type": "string",
                                "description": "Filter by provider",
                            },
                            "group_by": {
                                "type": "string",
                                "description": "Group by field (model, provider)",
                                "default": "model",
                            },
                        },
                    },
                ),
                Tool(
                    name="save_conversation",
                    description="Save a conversation for later retrieval",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Conversation title",
                            },
                            "model": {
                                "type": "string",
                                "description": "Model used",
                            },
                            "provider": {
                                "type": "string",
                                "description": "Provider used",
                            },
                            "messages": {
                                "type": "array",
                                "description": "Conversation messages",
                            },
                        },
                        "required": ["title", "model", "provider", "messages"],
                    },
                ),
                Tool(
                    name="list_conversations",
                    description="List saved conversations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "default": 50,
                            },
                            "offset": {
                                "type": "integer",
                                "default": 0,
                            },
                        },
                    },
                ),
                Tool(
                    name="health_check",
                    description="Check health status of all providers",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "list_models":
                    return await self._handle_list_models(arguments)
                elif name == "get_model_info":
                    return await self._handle_get_model_info(arguments)
                elif name == "generate":
                    return await self._handle_generate(arguments)
                elif name == "compare_models":
                    return await self._handle_compare_models(arguments)
                elif name == "get_usage_stats":
                    return await self._handle_get_usage_stats(arguments)
                elif name == "save_conversation":
                    return await self._handle_save_conversation(arguments)
                elif name == "list_conversations":
                    return await self._handle_list_conversations(arguments)
                elif name == "health_check":
                    return await self._handle_health_check(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="stats://usage",
                    name="Usage Statistics",
                    mimeType="application/json",
                    description="Overall usage statistics across all models",
                ),
                Resource(
                    uri="config://providers",
                    name="Provider Configuration",
                    mimeType="application/json",
                    description="Configuration status of all providers",
                ),
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource."""
            if uri == "stats://usage":
                stats = await self.database.get_aggregated_stats("model")
                import json
                return json.dumps(stats, indent=2)
            elif uri == "config://providers":
                providers_status = {}
                for name, provider in self.providers.items():
                    health = await provider.health_check()
                    providers_status[name] = health
                import json
                return json.dumps(providers_status, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def _handle_list_models(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle list_models tool."""
        provider_filter = arguments.get("provider")
        capability_filter = arguments.get("capability")
        
        all_models = []
        for provider_name, provider in self.providers.items():
            if provider_filter and provider_name != provider_filter:
                continue
            
            models = await provider.list_models()
            for model in models:
                if capability_filter:
                    cap = ModelCapability(capability_filter)
                    if cap not in model.capabilities:
                        continue
                all_models.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "provider": model.provider,
                    "context_length": model.context_length,
                    "capabilities": [c.value for c in model.capabilities],
                    "is_local": model.is_local,
                    "cost_per_1k_input": model.cost_per_1k_input_tokens,
                    "cost_per_1k_output": model.cost_per_1k_output_tokens,
                })
        
        import json
        return [TextContent(
            type="text",
            text=json.dumps(all_models, indent=2)
        )]

    async def _handle_get_model_info(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_model_info tool."""
        model_name = arguments["model"]
        provider_name = arguments["provider"]
        
        if provider_name not in self.providers:
            return [TextContent(type="text", text=f"Provider {provider_name} not found")]
        
        provider = self.providers[provider_name]
        model_info = await provider.get_model_info(model_name)
        
        if not model_info:
            return [TextContent(type="text", text=f"Model {model_name} not found")]
        
        import json
        return [TextContent(
            type="text",
            text=json.dumps({
                "name": model_info.name,
                "display_name": model_info.display_name,
                "provider": model_info.provider,
                "context_length": model_info.context_length,
                "capabilities": [c.value for c in model_info.capabilities],
                "is_local": model_info.is_local,
                "cost_per_1k_input": model_info.cost_per_1k_input_tokens,
                "cost_per_1k_output": model_info.cost_per_1k_output_tokens,
            }, indent=2)
        )]

    async def _handle_generate(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle generate tool."""
        model_name = arguments["model"]
        provider_name = arguments["provider"]
        
        if provider_name not in self.providers:
            return [TextContent(type="text", text=f"Provider {provider_name} not found")]
        
        provider = self.providers[provider_name]
        
        request = GenerationRequest(
            model=model_name,
            prompt=arguments.get("prompt"),
            messages=arguments.get("messages"),
            system_prompt=arguments.get("system_prompt"),
            max_tokens=arguments.get("max_tokens"),
            temperature=arguments.get("temperature", 0.7),
        )
        
        response = await provider.generate(request)
        
        # Log usage
        if self.config.should_track_costs():
            await self.database.log_usage(
                model=response.model,
                provider=response.provider,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
                cost=response.cost,
                latency_ms=response.latency_ms,
            )
        
        return [TextContent(
            type="text",
            text=f"{response.content}\n\n---\nTokens: {response.total_tokens} | Cost: ${response.cost:.4f} | Latency: {response.latency_ms:.0f}ms"
        )]

    async def _handle_compare_models(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle compare_models tool."""
        models = arguments["models"]
        prompt = arguments["prompt"]
        temperature = arguments.get("temperature", 0.7)
        
        results = []
        for model_spec in models:
            model_name = model_spec["model"]
            provider_name = model_spec["provider"]
            
            if provider_name not in self.providers:
                results.append({
                    "model": model_name,
                    "provider": provider_name,
                    "error": "Provider not found",
                })
                continue
            
            try:
                provider = self.providers[provider_name]
                request = GenerationRequest(
                    model=model_name,
                    prompt=prompt,
                    temperature=temperature,
                )
                
                response = await provider.generate(request)
                
                results.append({
                    "model": model_name,
                    "provider": provider_name,
                    "content": response.content,
                    "tokens": response.total_tokens,
                    "cost": response.cost,
                    "latency_ms": response.latency_ms,
                })
                
                # Log usage
                if self.config.should_track_costs():
                    await self.database.log_usage(
                        model=response.model,
                        provider=response.provider,
                        input_tokens=response.input_tokens,
                        output_tokens=response.output_tokens,
                        total_tokens=response.total_tokens,
                        cost=response.cost,
                        latency_ms=response.latency_ms,
                    )
            except Exception as e:
                results.append({
                    "model": model_name,
                    "provider": provider_name,
                    "error": str(e),
                })
        
        import json
        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    async def _handle_get_usage_stats(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_usage_stats tool."""
        group_by = arguments.get("group_by", "model")
        stats = await self.database.get_aggregated_stats(group_by)
        
        import json
        return [TextContent(type="text", text=json.dumps(stats, indent=2))]

    async def _handle_save_conversation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle save_conversation tool."""
        conversation_id = str(uuid.uuid4())
        
        await self.database.save_conversation(
            conversation_id=conversation_id,
            title=arguments["title"],
            model=arguments["model"],
            provider=arguments["provider"],
            messages=arguments["messages"],
        )
        
        return [TextContent(
            type="text",
            text=f"Conversation saved with ID: {conversation_id}"
        )]

    async def _handle_list_conversations(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle list_conversations tool."""
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)
        
        conversations = await self.database.list_conversations(limit, offset)
        
        import json
        return [TextContent(type="text", text=json.dumps(conversations, indent=2))]

    async def _handle_health_check(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle health_check tool."""
        health_status = {}
        
        for provider_name, provider in self.providers.items():
            health = await provider.health_check()
            health_status[provider_name] = health
        
        import json
        return [TextContent(type="text", text=json.dumps(health_status, indent=2))]

    async def run(self) -> None:
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def main():
    """Main entry point."""
    server = AIModelManagerServer()
    await server.initialize()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
