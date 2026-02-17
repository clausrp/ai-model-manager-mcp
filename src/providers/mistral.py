"""Mistral AI provider implementation."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import ChatMessage

from ..models.base import (
    ModelProvider,
    ModelInfo,
    ModelCapability,
    GenerationRequest,
    GenerationResponse,
)


class MistralProvider(ModelProvider):
    """Provider for Mistral AI models."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("mistral", config)
        self.api_key = config.get("api_key")
        
        if not self.api_key:
            raise ValueError("Mistral API key is required")
        
        self.client = MistralAsyncClient(api_key=self.api_key)
        
        # Model definitions
        self.model_definitions = {
            "mistral-large-latest": {
                "display_name": "Mistral Large",
                "context_length": 128000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "cost_per_1k_input_tokens": 0.002,
                "cost_per_1k_output_tokens": 0.006,
            },
            "mistral-small-latest": {
                "display_name": "Mistral Small",
                "context_length": 32000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                ],
                "cost_per_1k_input_tokens": 0.0002,
                "cost_per_1k_output_tokens": 0.0006,
            },
            "mistral-medium-latest": {
                "display_name": "Mistral Medium",
                "context_length": 32000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                ],
                "cost_per_1k_input_tokens": 0.0027,
                "cost_per_1k_output_tokens": 0.0081,
            },
        }

    async def list_models(self) -> List[ModelInfo]:
        """List available Mistral models."""
        models = []
        for model_name, model_def in self.model_definitions.items():
            models.append(
                ModelInfo(
                    name=model_name,
                    display_name=model_def["display_name"],
                    provider="mistral",
                    context_length=model_def["context_length"],
                    capabilities=model_def["capabilities"],
                    cost_per_1k_input_tokens=model_def["cost_per_1k_input_tokens"],
                    cost_per_1k_output_tokens=model_def["cost_per_1k_output_tokens"],
                    is_local=False,
                )
            )
        return models

    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific Mistral model."""
        if model_name in self.model_definitions:
            model_def = self.model_definitions[model_name]
            return ModelInfo(
                name=model_name,
                display_name=model_def["display_name"],
                provider="mistral",
                context_length=model_def["context_length"],
                capabilities=model_def["capabilities"],
                cost_per_1k_input_tokens=model_def["cost_per_1k_input_tokens"],
                cost_per_1k_output_tokens=model_def["cost_per_1k_output_tokens"],
                is_local=False,
            )
        return None

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Mistral AI."""
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = []
            if request.system_prompt:
                messages.append(ChatMessage(role="system", content=request.system_prompt))
            
            if request.messages:
                for msg in request.messages:
                    messages.append(
                        ChatMessage(
                            role=msg.get("role", "user"),
                            content=msg.get("content", "")
                        )
                    )
            elif request.prompt:
                messages.append(ChatMessage(role="user", content=request.prompt))
            
            # Generate response
            response = await self.client.chat(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens,
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            content = response.choices[0].message.content if response.choices else ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            # Calculate cost
            model_info = await self.get_model_info(request.model)
            cost = self.calculate_cost(model_info, input_tokens, output_tokens) if model_info else 0.0
            
            return GenerationResponse(
                model=request.model,
                content=content,
                provider="mistral",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                finish_reason=response.choices[0].finish_reason if response.choices else None,
                metadata={
                    "id": response.id,
                    "model": response.model,
                },
            )
        except Exception as e:
            raise Exception(f"Mistral generation error: {str(e)}")

    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[str]:
        """Generate text with streaming response."""
        try:
            # Prepare messages
            messages = []
            if request.system_prompt:
                messages.append(ChatMessage(role="system", content=request.system_prompt))
            
            if request.messages:
                for msg in request.messages:
                    messages.append(
                        ChatMessage(
                            role=msg.get("role", "user"),
                            content=msg.get("content", "")
                        )
                    )
            elif request.prompt:
                messages.append(ChatMessage(role="user", content=request.prompt))
            
            # Stream response
            async for chunk in self.client.chat_stream(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens,
            ):
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"Mistral streaming error: {str(e)}")

    async def is_available(self) -> bool:
        """Check if Mistral API is available."""
        try:
            await self.client.list_models()
            return True
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Mistral API."""
        try:
            models = await self.client.list_models()
            return {
                "status": "healthy",
                "available": True,
                "provider": "mistral",
                "models_count": len(models.data) if models else 0,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "available": False,
                "provider": "mistral",
                "error": str(e),
            }

# Made with Bob
