"""Base classes and interfaces for model providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, AsyncIterator
from enum import Enum


class ModelCapability(str, Enum):
    """Model capabilities."""
    CHAT = "chat"
    COMPLETION = "completion"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    CODE = "code"


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    display_name: str
    provider: str
    context_length: int
    capabilities: List[ModelCapability]
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0
    is_local: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRequest:
    """Request for text generation."""
    model: str
    prompt: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    top_p: float = 1.0
    stream: bool = False
    system_prompt: Optional[str] = None
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResponse:
    """Response from text generation."""
    model: str
    content: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    latency_ms: float
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageStats:
    """Usage statistics for a model."""
    model: str
    provider: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    average_latency_ms: float
    error_count: int
    last_used: Optional[str] = None


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models from this provider."""
        pass

    @abstractmethod
    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        pass

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using the specified model."""
        pass

    @abstractmethod
    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[str]:
        """Generate text with streaming response."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the provider."""
        pass

    def calculate_cost(
        self, model_info: ModelInfo, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate the cost for a generation request."""
        if model_info.is_local:
            return 0.0
        
        input_cost = (input_tokens / 1000) * model_info.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * model_info.cost_per_1k_output_tokens
        return input_cost + output_cost

# Made with Bob
