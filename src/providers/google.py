"""Google Gemini provider implementation."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
import google.generativeai as genai

from ..models.base import (
    ModelProvider,
    ModelInfo,
    ModelCapability,
    GenerationRequest,
    GenerationResponse,
)


class GoogleProvider(ModelProvider):
    """Provider for Google Gemini models."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("google", config)
        self.api_key = config.get("api_key")
        
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=self.api_key)
        
        # Model definitions
        self.model_definitions = {
            "gemini-1.5-pro": {
                "display_name": "Gemini 1.5 Pro",
                "context_length": 2000000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "cost_per_1k_input_tokens": 0.00125,
                "cost_per_1k_output_tokens": 0.005,
            },
            "gemini-1.5-flash": {
                "display_name": "Gemini 1.5 Flash",
                "context_length": 1000000,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "cost_per_1k_input_tokens": 0.000075,
                "cost_per_1k_output_tokens": 0.0003,
            },
            "gemini-pro": {
                "display_name": "Gemini Pro",
                "context_length": 32760,
                "capabilities": [
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                ],
                "cost_per_1k_input_tokens": 0.0005,
                "cost_per_1k_output_tokens": 0.0015,
            },
        }

    async def list_models(self) -> List[ModelInfo]:
        """List available Google Gemini models."""
        models = []
        for model_name, model_def in self.model_definitions.items():
            models.append(
                ModelInfo(
                    name=model_name,
                    display_name=model_def["display_name"],
                    provider="google",
                    context_length=model_def["context_length"],
                    capabilities=model_def["capabilities"],
                    cost_per_1k_input_tokens=model_def["cost_per_1k_input_tokens"],
                    cost_per_1k_output_tokens=model_def["cost_per_1k_output_tokens"],
                    is_local=False,
                )
            )
        return models

    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific Google model."""
        if model_name in self.model_definitions:
            model_def = self.model_definitions[model_name]
            return ModelInfo(
                name=model_name,
                display_name=model_def["display_name"],
                provider="google",
                context_length=model_def["context_length"],
                capabilities=model_def["capabilities"],
                cost_per_1k_input_tokens=model_def["cost_per_1k_input_tokens"],
                cost_per_1k_output_tokens=model_def["cost_per_1k_output_tokens"],
                is_local=False,
            )
        return None

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Google Gemini."""
        start_time = time.time()
        
        try:
            model = genai.GenerativeModel(request.model)
            
            # Prepare prompt
            if request.messages:
                # Convert messages to Gemini format
                prompt_parts = []
                for msg in request.messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "system":
                        prompt_parts.append(f"System: {content}")
                    elif role == "user":
                        prompt_parts.append(f"User: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
                prompt = "\n".join(prompt_parts)
            else:
                prompt = request.prompt or ""
            
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{prompt}"
            
            # Generate response
            generation_config = genai.types.GenerationConfig(
                temperature=request.temperature,
                top_p=request.top_p,
                max_output_tokens=request.max_tokens,
                stop_sequences=request.stop_sequences,
            )
            
            response = await model.generate_content_async(
                prompt,
                generation_config=generation_config,
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            content = response.text if response.text else ""
            
            # Extract token counts (Gemini provides these in usage_metadata)
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, "usage_metadata"):
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0
            
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            model_info = await self.get_model_info(request.model)
            cost = self.calculate_cost(model_info, input_tokens, output_tokens) if model_info else 0.0
            
            return GenerationResponse(
                model=request.model,
                content=content,
                provider="google",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                finish_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
                metadata={
                    "model": request.model,
                },
            )
        except Exception as e:
            raise Exception(f"Google generation error: {str(e)}")

    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[str]:
        """Generate text with streaming response."""
        try:
            model = genai.GenerativeModel(request.model)
            
            # Prepare prompt
            if request.messages:
                prompt_parts = []
                for msg in request.messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "system":
                        prompt_parts.append(f"System: {content}")
                    elif role == "user":
                        prompt_parts.append(f"User: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
                prompt = "\n".join(prompt_parts)
            else:
                prompt = request.prompt or ""
            
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{prompt}"
            
            # Generate response
            generation_config = genai.types.GenerationConfig(
                temperature=request.temperature,
                top_p=request.top_p,
                max_output_tokens=request.max_tokens,
                stop_sequences=request.stop_sequences,
            )
            
            response = await model.generate_content_async(
                prompt,
                generation_config=generation_config,
                stream=True,
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Google streaming error: {str(e)}")

    async def is_available(self) -> bool:
        """Check if Google API is available."""
        try:
            models = genai.list_models()
            return len(list(models)) > 0
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Google API."""
        try:
            available = await self.is_available()
            return {
                "status": "healthy" if available else "unhealthy",
                "available": available,
                "provider": "google",
                "models_count": len(self.model_definitions),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "available": False,
                "provider": "google",
                "error": str(e),
            }

# Made with Bob
