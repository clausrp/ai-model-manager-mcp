# Architecture Documentation

## Overview

The AI Model Manager MCP Server is designed as a modular, extensible system for managing and interfacing with multiple AI model providers through a unified API.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Client (Claude, etc.)                │
└───────────────────────────┬─────────────────────────────────┘
                            │ MCP Protocol (stdio)
┌───────────────────────────▼─────────────────────────────────┐
│                      MCP Server Layer                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tools: list_models, generate, compare_models, etc.   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Resources: stats://usage, config://providers         │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Provider Manager                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Ollama  │  │  OpenAI  │  │Anthropic │  │  Google  │   │
│  │ Provider │  │ Provider │  │ Provider │  │ Provider │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
┌───────▼─────┐ ┌─────▼──────┐ ┌───▼──────┐ ┌───▼──────┐
│   Ollama    │ │  OpenAI    │ │ Anthropic│ │  Google  │
│   Server    │ │    API     │ │   API    │ │   API    │
└─────────────┘ └────────────┘ └──────────┘ └──────────┘
```

## Core Components

### 1. MCP Server (`src/server.py`)

**Responsibilities:**
- Handle MCP protocol communication
- Route tool calls to appropriate handlers
- Manage provider lifecycle
- Coordinate between components

**Key Methods:**
- `initialize()`: Set up providers and database
- `_register_handlers()`: Register MCP tools and resources
- `call_tool()`: Route tool calls to handlers

### 2. Model Providers (`src/providers/`)

**Base Interface (`models/base.py`):**
```python
class ModelProvider(ABC):
    async def list_models() -> List[ModelInfo]
    async def get_model_info(model_name) -> ModelInfo
    async def generate(request) -> GenerationResponse
    async def generate_stream(request) -> AsyncIterator[str]
    async def is_available() -> bool
    async def health_check() -> Dict[str, Any]
```

**Provider Implementations:**
- `OllamaProvider`: Local models via Ollama
- `OpenAIProvider`: OpenAI GPT models
- `AnthropicProvider`: Claude models
- `GoogleProvider`: Gemini models
- `MistralProvider`: Mistral AI models

### 3. Storage Layer (`src/storage/`)

**Database (`storage/database.py`):**
- SQLite for persistent storage
- Tables:
  - `usage_stats`: Token usage and costs
  - `conversations`: Saved conversations
  - `api_keys`: Provider credentials
  - `model_preferences`: User preferences

**Configuration (`storage/config.py`):**
- Environment variable management
- Provider configuration
- Model definitions from JSON

### 4. Data Models (`src/models/base.py`)

**Core Models:**
- `ModelInfo`: Model metadata and capabilities
- `GenerationRequest`: Request parameters
- `GenerationResponse`: Response with metrics
- `UsageStats`: Usage tracking data

## Data Flow

### Generation Request Flow

```
1. Client sends MCP tool call "generate"
   ↓
2. Server validates and routes to _handle_generate()
   ↓
3. Handler creates GenerationRequest
   ↓
4. Provider.generate() called
   ↓
5. Provider makes API/local call
   ↓
6. Response processed and metrics calculated
   ↓
7. Usage logged to database (if enabled)
   ↓
8. Response returned to client
```

### Model Comparison Flow

```
1. Client requests comparison across N models
   ↓
2. Server creates N parallel generation requests
   ↓
3. Each provider generates independently
   ↓
4. Results aggregated with metrics
   ↓
5. Comparison data returned to client
```

## Configuration Management

### Environment Variables
```
.env file → Config class → Provider initialization
```

### Model Definitions
```
config/models.json → Config class → Provider model info
```

## Database Schema

### usage_stats
```sql
CREATE TABLE usage_stats (
    id INTEGER PRIMARY KEY,
    model TEXT,
    provider TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost REAL,
    latency_ms REAL,
    timestamp TEXT,
    metadata TEXT
)
```

### conversations
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    model TEXT,
    provider TEXT,
    messages TEXT,  -- JSON array
    created_at TEXT,
    updated_at TEXT,
    metadata TEXT
)
```

## Extension Points

### Adding a New Provider

1. Create provider class in `src/providers/`:
```python
class NewProvider(ModelProvider):
    def __init__(self, config):
        super().__init__("new_provider", config)
    
    async def list_models(self):
        # Implementation
    
    # ... implement other methods
```

2. Add to `src/providers/__init__.py`:
```python
from .new_provider import NewProvider
__all__ = [..., "NewProvider"]
```

3. Add initialization in `server.py`:
```python
if self.config.is_provider_configured("new_provider"):
    config = self.config.get_provider_config("new_provider")
    self.providers["new_provider"] = NewProvider(config)
```

4. Add configuration in `.env.example`:
```env
NEW_PROVIDER_API_KEY=your_key_here
```

### Adding a New Tool

1. Add tool definition in `_register_handlers()`:
```python
Tool(
    name="new_tool",
    description="Description",
    inputSchema={...}
)
```

2. Add handler method:
```python
async def _handle_new_tool(self, arguments):
    # Implementation
    return [TextContent(type="text", text=result)]
```

3. Route in `call_tool()`:
```python
elif name == "new_tool":
    return await self._handle_new_tool(arguments)
```

## Performance Considerations

### Async Operations
- All I/O operations are async
- Providers can be called concurrently
- Database operations are non-blocking

### Caching Strategy
- Model lists cached per provider
- Configuration loaded once at startup
- Database connection pooling via aiosqlite

### Rate Limiting
- Configurable per-provider limits
- Token bucket algorithm (future)
- Automatic retry with backoff

## Security

### API Key Management
- Stored in environment variables
- Never logged or exposed
- Database encryption recommended for production

### Input Validation
- All tool inputs validated
- SQL injection prevention via parameterized queries
- JSON schema validation for requests

## Error Handling

### Provider Errors
```python
try:
    response = await provider.generate(request)
except Exception as e:
    logger.error(f"Provider error: {e}")
    # Fallback or error response
```

### Database Errors
- Automatic retry for transient errors
- Graceful degradation if database unavailable
- Error logging for debugging

## Monitoring

### Metrics Collected
- Request count per model/provider
- Token usage (input/output)
- Cost per request
- Latency per request
- Error rates

### Health Checks
- Provider availability
- Database connectivity
- API key validity
- Model availability

## Future Enhancements

### Smart Routing
- Task complexity analysis
- Cost-based routing
- Performance-based selection
- Load balancing

### Advanced Features
- Model fine-tuning workflows
- Batch processing
- Streaming aggregation
- Real-time dashboards

### Scalability
- Multi-instance support
- Distributed caching
- Message queue integration
- Horizontal scaling

## Testing Strategy

### Unit Tests
- Provider implementations
- Database operations
- Configuration management

### Integration Tests
- End-to-end tool calls
- Provider interactions
- Database persistence

### Performance Tests
- Concurrent request handling
- Large conversation management
- Database query optimization

## Deployment

### Local Development
```bash
python -m src.server
```

### Production Considerations
- Use process manager (systemd, supervisor)
- Enable database encryption
- Configure logging
- Set up monitoring
- Implement rate limiting

## Dependencies

### Core
- `mcp`: MCP protocol implementation
- `aiohttp`: Async HTTP client
- `aiosqlite`: Async SQLite

### Providers
- `ollama`: Ollama client
- `openai`: OpenAI API
- `anthropic`: Anthropic API
- `google-generativeai`: Google Gemini
- `mistralai`: Mistral AI

### Utilities
- `pydantic`: Data validation
- `tiktoken`: Token counting
- `python-dotenv`: Environment management