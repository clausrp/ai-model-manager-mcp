"""Configuration management."""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ProviderConfig(BaseModel):
    """Configuration for a model provider."""
    api_key: Optional[str] = None
    host: Optional[str] = None
    timeout: int = 120
    enabled: bool = True


class ServerConfig(BaseSettings):
    """Server configuration from environment variables."""
    
    # OpenAI
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    openai_org_id: Optional[str] = Field(None, alias="OPENAI_ORG_ID")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    
    # Google
    google_api_key: Optional[str] = Field(None, alias="GOOGLE_API_KEY")
    
    # Mistral
    mistral_api_key: Optional[str] = Field(None, alias="MISTRAL_API_KEY")
    
    # Ollama
    ollama_host: str = Field("http://localhost:11434", alias="OLLAMA_HOST")
    ollama_timeout: int = Field(120, alias="OLLAMA_TIMEOUT")
    
    # Database
    database_path: str = Field("./data/models.db", alias="DATABASE_PATH")
    
    # Server
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    max_retries: int = Field(3, alias="MAX_RETRIES")
    request_timeout: int = Field(60, alias="REQUEST_TIMEOUT")
    
    # Cost tracking
    enable_cost_tracking: bool = Field(True, alias="ENABLE_COST_TRACKING")
    cost_alert_threshold: float = Field(10.0, alias="COST_ALERT_THRESHOLD")
    
    # Smart routing
    enable_smart_routing: bool = Field(True, alias="ENABLE_SMART_ROUTING")
    prefer_local_models: bool = Field(True, alias="PREFER_LOCAL_MODELS")
    fallback_to_cloud: bool = Field(True, alias="FALLBACK_TO_CLOUD")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(True, alias="RATE_LIMIT_ENABLED")
    requests_per_minute: int = Field(60, alias="REQUESTS_PER_MINUTE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class Config:
    """Configuration manager."""

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.server_config = ServerConfig()
        self.models_config: Dict[str, Any] = {}
        self._load_models_config()

    def _load_models_config(self) -> None:
        """Load models configuration from JSON file."""
        models_file = self.config_dir / "models.json"
        if models_file.exists():
            with open(models_file, "r") as f:
                self.models_config = json.load(f)

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        config: Dict[str, Any] = {}
        
        if provider == "ollama":
            config = {
                "host": self.server_config.ollama_host,
                "timeout": self.server_config.ollama_timeout,
            }
        elif provider == "openai":
            config = {
                "api_key": self.server_config.openai_api_key,
                "org_id": self.server_config.openai_org_id,
            }
        elif provider == "anthropic":
            config = {
                "api_key": self.server_config.anthropic_api_key,
            }
        elif provider == "google":
            config = {
                "api_key": self.server_config.google_api_key,
            }
        elif provider == "mistral":
            config = {
                "api_key": self.server_config.mistral_api_key,
            }
        
        return config

    def get_model_info(self, provider: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model information from configuration."""
        if provider in ["ollama"]:
            models = self.models_config.get("local_models", {}).get(provider, {})
        else:
            models = self.models_config.get("cloud_models", {}).get(provider, {})
        
        return models.get(model_name)

    def list_configured_providers(self) -> list[str]:
        """List all configured providers."""
        providers = []
        
        if self.server_config.ollama_host:
            providers.append("ollama")
        if self.server_config.openai_api_key:
            providers.append("openai")
        if self.server_config.anthropic_api_key:
            providers.append("anthropic")
        if self.server_config.google_api_key:
            providers.append("google")
        if self.server_config.mistral_api_key:
            providers.append("mistral")
        
        return providers

    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is configured."""
        return provider in self.list_configured_providers()

    def get_database_path(self) -> str:
        """Get database path."""
        return self.server_config.database_path

    def should_track_costs(self) -> bool:
        """Check if cost tracking is enabled."""
        return self.server_config.enable_cost_tracking

    def get_cost_alert_threshold(self) -> float:
        """Get cost alert threshold."""
        return self.server_config.cost_alert_threshold

    def is_smart_routing_enabled(self) -> bool:
        """Check if smart routing is enabled."""
        return self.server_config.enable_smart_routing

    def should_prefer_local_models(self) -> bool:
        """Check if local models should be preferred."""
        return self.server_config.prefer_local_models

    def should_fallback_to_cloud(self) -> bool:
        """Check if fallback to cloud is enabled."""
        return self.server_config.fallback_to_cloud

# Made with Bob
