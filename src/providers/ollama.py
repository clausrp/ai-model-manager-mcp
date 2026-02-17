"""Ollama provider implementation."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
import ollama
from ollama import AsyncClient

from ..models.base import (
    ModelProvider,
    ModelInfo,
    ModelCapability,
    GenerationRequest,
    GenerationResponse,
)


class OllamaProvider(ModelProvider):
    """Provider for Ollama local models."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("ollama", config)
        self.host = config.get("host", "http://localhost:11434")
        self.timeout = config.get("timeout", 120)
        self.client = AsyncClient(host=self.host, timeout=self.timeout)

    async def list_models(self) -> List[ModelInfo]:
        """List available Ollama models."""
        try:
            response = await self.client.list()
            models = []
            
            for model in response.get("models", []):
                model_name = model.get("name", "").split(":")[0]
                
                # Determine capabilities based on model name
                capabilities = [ModelCapability.CHAT, ModelCapability.COMPLETION]
                if "code" in model_name.lower():
                    capabilities.append(ModelCapability.CODE)
                if "vision" in model_name.lower() or "llava" in model_name.lower():
                    capabilities.append(ModelCapability.VISION)
                
                models.append(
                    ModelInfo(
                        name=model.get("name", ""),
                        display_name=model_name.title(),
                        provider="ollama",
                        context_length=model.get("details", {}).get("parameter_size", 4096),
                        capabilities=capabilities,
                        is_local=True,
                        metadata={
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at", ""),
                            "digest": model.get("digest", ""),
                        },
                    )
                )
            
            return models
        except Exception as e:
            print(f"Error listing Ollama models: {e}")
            return []

    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific Ollama model."""
        models = await self.list_models()
        for model in models:
            if model.name == model_name or model.name.startswith(f"{model_name}:"):
                return model
        return None

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Ollama."""
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
            response = await self.client.chat(
                model=request.model,
                messages=messages,
                options={
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_predict": request.max_tokens or -1,
                    "stop": request.stop_sequences or [],
                },
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            content = response.get("message", {}).get("content", "")
            input_tokens = response.get("prompt_eval_count", 0)
            output_tokens = response.get("eval_count", 0)
            
            return GenerationResponse(
                model=request.model,
                content=content,
                provider="ollama",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost=0.0,  # Local models are free
                latency_ms=latency_ms,
                finish_reason=response.get("done_reason"),
                metadata={
                    "total_duration": response.get("total_duration", 0),
                    "load_duration": response.get("load_duration", 0),
                    "prompt_eval_duration": response.get("prompt_eval_duration", 0),
                    "eval_duration": response.get("eval_duration", 0),
                },
            )
        except Exception as e:
            raise Exception(f"Ollama generation error: {str(e)}")

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
            async for chunk in await self.client.chat(
                model=request.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_predict": request.max_tokens or -1,
                    "stop": request.stop_sequences or [],
                },
            ):
                if content := chunk.get("message", {}).get("content"):
                    yield content
        except Exception as e:
            raise Exception(f"Ollama streaming error: {str(e)}")

    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            await self.client.list()
            return True
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Ollama."""
        try:
            models = await self.list_models()
            return {
                "status": "healthy",
                "available": True,
                "host": self.host,
                "models_count": len(models),
                "models": [m.name for m in models],
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "available": False,
                "host": self.host,
                "error": str(e),
            }

    async def pull_model(self, model_name: str) -> AsyncIterator[Dict[str, Any]]:
        """Pull/download a model from Ollama registry."""
        try:
            async for progress in await self.client.pull(model_name, stream=True):
                yield progress
        except Exception as e:
            raise Exception(f"Error pulling model {model_name}: {str(e)}")

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from local storage."""
        try:
            await self.client.delete(model_name)
            return True
        except Exception as e:
            print(f"Error deleting model {model_name}: {e}")
            return False

# Made with Bob
