"""Anthropic provider implementation."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
from anthropic import AsyncAnthropic

from ..models.base import (
    ModelProvider,
    ModelInfo,
    ModelCapability,
    GenerationRequest,
    GenerationResponse,
)


class AnthropicProvider(ModelProvider):
    """Provider for Anthropic Claude models."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("anthropic", config)
        self.api_key = config.get("api_key")
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        
        # Model definitions
        self.model_definitions = {
            "claude-3-5-sonnet-20241022": {
                "display_name": "Claude 3.5 Sonnet",
                "context_length": 200000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "cost_per_1k_input_tokens": 0.003,
                "cost_per_1k_output_tokens": 0.015,
            },
            "claude-3-opus-20240229": {
                "display_name": "Claude 3 Opus",
                "context_length": 200000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.VISION,
                ],
                "cost_per_1k_input_tokens": 0.015,
                "cost_per_1k_output_tokens": 0.075,
            },
            "claude-3-haiku-20240307": {
                "display_name": "Claude 3 Haiku",
                "context_length": 200000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.VISION,
                ],
                "cost_per_1k_input_tokens": 0.00025,
                "cost_per_1k_output_tokens": 0.00125,
            },
        }

    async def list_models(self) -> List[ModelInfo]:
        """List available Anthropic models."""
        models = []
        for model_name, model_def in self.model_definitions.items():
            models.append(
                ModelInfo(
                    name=model_name,
                    display_name=model_def["display_name"],
                    provider="anthropic",
                    context_length=model_def["context_length"],
                    capabilities=model_def["capabilities"],
                    cost_per_1k_input_tokens=model_def["cost_per_1k_input_tokens"],
                    cost_per_1k_output_tokens=model_def["cost_per_1k_output_tokens"],
                    is_local=False,
                )
            )
        return models

    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific Anthropic model."""
        if model_name in self.model_definitions:
            model_def = self.model_definitions[model_name]
            return ModelInfo(
                name=model_name,
                display_name=model_def["display_name"],
                provider="anthropic",
                context_length=model_def["context_length"],
                capabilities=model_def["capabilities"],
                cost_per_1k_input_tokens=model_def["cost_per_1k_input_tokens"],
                cost_per_1k_output_tokens=model_def["cost_per_1k_output_tokens"],
                is_local=False,
            )
        return None

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Anthropic Claude."""
        start_time = time.time()
        
        try:
            # Prepare messages (Claude doesn't use system in messages array)
            messages = []
            if request.messages:
                messages.extend(request.messages)
            elif request.prompt:
                messages.append({"role": "user", "content": request.prompt})
            
            # Generate response
            response = await self.client.messages.create(
                model=request.model,
                max_tokens=request.max_tokens or 4096,
                messages=messages,
                system=request.system_prompt,
                temperature=request.temperature,
                top_p=request.top_p,
                stop_sequences=request.stop_sequences,
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
            
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            model_info = await self.get_model_info(request.model)
            cost = self.calculate_cost(model_info, input_tokens, output_tokens) if model_info else 0.0
            
            return GenerationResponse(
                model=request.model,
                content=content,
                provider="anthropic",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                finish_reason=response.stop_reason,
                metadata={
                    "id": response.id,
                    "model": response.model,
                    "type": response.type,
                },
            )
        except Exception as e:
            raise Exception(f"Anthropic generation error: {str(e)}")

    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[str]:
        """Generate text with streaming response."""
        try:
            # Prepare messages
            messages = []
            if request.messages:
                messages.extend(request.messages)
            elif request.prompt:
                messages.append({"role": "user", "content": request.prompt})
            
            # Stream response
            async with self.client.messages.stream(
                model=request.model,
                max_tokens=request.max_tokens or 4096,
                messages=messages,
                system=request.system_prompt,
                temperature=request.temperature,
                top_p=request.top_p,
                stop_sequences=request.stop_sequences,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise Exception(f"Anthropic streaming error: {str(e)}")

    async def is_available(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            # Try a minimal request to check availability
            await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Anthropic API."""
        try:
            available = await self.is_available()
            return {
                "status": "healthy" if available else "unhealthy",
                "available": available,
                "provider": "anthropic",
                "models_count": len(self.model_definitions),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "available": False,
                "provider": "anthropic",
                "error": str(e),
            }

# Made with Bob
