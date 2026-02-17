"""OpenAI provider implementation."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
from openai import AsyncOpenAI

from ..models.base import (
    ModelProvider,
    ModelInfo,
    ModelCapability,
    GenerationRequest,
    GenerationResponse,
)


class OpenAIProvider(ModelProvider):
    """Provider for OpenAI API models."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("openai", config)
        self.api_key = config.get("api_key")
        self.org_id = config.get("org_id")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.org_id,
        )
        
        # Model definitions with capabilities and pricing
        self.model_definitions = {
            "gpt-4o": {
                "display_name": "GPT-4o",
                "context_length": 128000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "cost_per_1k_input_tokens": 0.0025,
                "cost_per_1k_output_tokens": 0.01,
            },
            "gpt-4o-mini": {
                "display_name": "GPT-4o Mini",
                "context_length": 128000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "cost_per_1k_input_tokens": 0.00015,
                "cost_per_1k_output_tokens": 0.0006,
            },
            "gpt-4-turbo": {
                "display_name": "GPT-4 Turbo",
                "context_length": 128000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "cost_per_1k_input_tokens": 0.01,
                "cost_per_1k_output_tokens": 0.03,
            },
            "gpt-3.5-turbo": {
                "display_name": "GPT-3.5 Turbo",
                "context_length": 16385,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "cost_per_1k_input_tokens": 0.0005,
                "cost_per_1k_output_tokens": 0.0015,
            },
        }

    async def list_models(self) -> List[ModelInfo]:
        """List available OpenAI models."""
        models = []
        for model_name, model_def in self.model_definitions.items():
            models.append(
                ModelInfo(
                    name=model_name,
                    display_name=model_def["display_name"],
                    provider="openai",
                    context_length=model_def["context_length"],
                    capabilities=model_def["capabilities"],
                    cost_per_1k_input_tokens=model_def["cost_per_1k_input_tokens"],
                    cost_per_1k_output_tokens=model_def["cost_per_1k_output_tokens"],
                    is_local=False,
                )
            )
        return models

    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific OpenAI model."""
        if model_name in self.model_definitions:
            model_def = self.model_definitions[model_name]
            return ModelInfo(
                name=model_name,
                display_name=model_def["display_name"],
                provider="openai",
                context_length=model_def["context_length"],
                capabilities=model_def["capabilities"],
                cost_per_1k_input_tokens=model_def["cost_per_1k_input_tokens"],
                cost_per_1k_output_tokens=model_def["cost_per_1k_output_tokens"],
                is_local=False,
            )
        return None

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using OpenAI."""
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            if request.messages:
                messages.extend(request.messages)
            elif request.prompt:
                messages.append({"role": "user", "content": request.prompt})
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=request.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop_sequences,
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            # Calculate cost
            model_info = await self.get_model_info(request.model)
            cost = self.calculate_cost(model_info, input_tokens, output_tokens) if model_info else 0.0
            
            return GenerationResponse(
                model=request.model,
                content=content,
                provider="openai",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "model": response.model,
                },
            )
        except Exception as e:
            raise Exception(f"OpenAI generation error: {str(e)}")

    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[str]:
        """Generate text with streaming response."""
        try:
            # Prepare messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            if request.messages:
                messages.extend(request.messages)
            elif request.prompt:
                messages.append({"role": "user", "content": request.prompt})
            
            # Stream response
            stream = await self.client.chat.completions.create(
                model=request.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop_sequences,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"OpenAI streaming error: {str(e)}")

    async def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on OpenAI API."""
        try:
            models = await self.client.models.list()
            return {
                "status": "healthy",
                "available": True,
                "provider": "openai",
                "models_count": len(list(models)),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "available": False,
                "provider": "openai",
                "error": str(e),
            }

# Made with Bob
