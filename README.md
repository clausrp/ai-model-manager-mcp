# AI Model Manager MCP Server

A powerful Model Context Protocol (MCP) server that provides unified access to both local AI models (via Ollama) and cloud-based models (OpenAI, Anthropic, Google Gemini, Mistral AI). This server enables intelligent model routing, cost tracking, and comprehensive model management.

## 🌟 Features

### Multi-Provider Support
- **Local Models**: Ollama (Llama, Mistral, CodeLlama, Phi-3, etc.)
- **Cloud APIs**: 
  - OpenAI (GPT-4o, GPT-4 Turbo, GPT-3.5)
  - Anthropic (Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku)
  - Google (Gemini 1.5 Pro, Gemini 1.5 Flash)
  - Mistral AI (Mistral Large, Mistral Small)

### Core Capabilities
- 🔄 **Unified Interface**: Single API for all model providers
- 💰 **Cost Tracking**: Automatic token counting and cost calculation
- 📊 **Usage Analytics**: Detailed statistics and performance metrics
- 🎯 **Smart Routing**: Intelligent model selection based on requirements
- 💬 **Conversation Management**: Save and restore conversation contexts
- ⚡ **Streaming Support**: Real-time response streaming
- 🔍 **Model Comparison**: Compare outputs across multiple models
- 🏥 **Health Monitoring**: Provider availability and status checks

## 📋 Prerequisites

- Python 3.10 or higher
- Ollama installed (for local models) - [Install Ollama](https://ollama.ai)
- API keys for cloud providers (optional)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the project directory
cd ai-model-manager-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required for cloud providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
MISTRAL_API_KEY=your_mistral_key_here

# Ollama configuration (if not using defaults)
OLLAMA_HOST=http://localhost:11434
```

### 3. Install Ollama Models (Optional)

```bash
# Install some popular local models
ollama pull llama3.2
ollama pull mistral
ollama pull codellama
```

### 4. Run the Server

```bash
python -m src.server
```

## 🔧 MCP Tools

### `list_models`
List all available models from configured providers.

**Parameters:**
- `provider` (optional): Filter by provider name
- `capability` (optional): Filter by capability (chat, completion, vision, etc.)

**Example:**
```json
{
  "provider": "ollama",
  "capability": "chat"
}
```

### `get_model_info`
Get detailed information about a specific model.

**Parameters:**
- `model` (required): Model name
- `provider` (required): Provider name

**Example:**
```json
{
  "model": "gpt-4o",
  "provider": "openai"
}
```

### `generate`
Generate text using a specified model.

**Parameters:**
- `model` (required): Model name
- `provider` (required): Provider name
- `prompt` (optional): Text prompt
- `messages` (optional): Chat messages array
- `system_prompt` (optional): System prompt
- `max_tokens` (optional): Maximum tokens to generate
- `temperature` (optional): Temperature (0-2, default: 0.7)

**Example:**
```json
{
  "model": "llama3.2",
  "provider": "ollama",
  "prompt": "Explain quantum computing in simple terms",
  "temperature": 0.7
}
```

### `compare_models`
Compare outputs from multiple models for the same prompt.

**Parameters:**
- `models` (required): Array of model/provider pairs
- `prompt` (required): Text prompt
- `temperature` (optional): Temperature (default: 0.7)

**Example:**
```json
{
  "models": [
    {"model": "llama3.2", "provider": "ollama"},
    {"model": "gpt-4o-mini", "provider": "openai"},
    {"model": "claude-3-haiku-20240307", "provider": "anthropic"}
  ],
  "prompt": "Write a haiku about programming"
}
```

### `get_usage_stats`
Get usage statistics and costs.

**Parameters:**
- `model` (optional): Filter by model
- `provider` (optional): Filter by provider
- `group_by` (optional): Group by field (model, provider)

**Example:**
```json
{
  "group_by": "provider"
}
```

### `save_conversation`
Save a conversation for later retrieval.

**Parameters:**
- `title` (required): Conversation title
- `model` (required): Model used
- `provider` (required): Provider used
- `messages` (required): Array of conversation messages

**Example:**
```json
{
  "title": "Python Tutorial Discussion",
  "model": "gpt-4o",
  "provider": "openai",
  "messages": [
    {"role": "user", "content": "How do I use async/await?"},
    {"role": "assistant", "content": "Async/await is..."}
  ]
}
```

### `list_conversations`
List saved conversations.

**Parameters:**
- `limit` (optional): Number of conversations (default: 50)
- `offset` (optional): Offset for pagination (default: 0)

### `health_check`
Check health status of all configured providers.

## 📚 MCP Resources

### `stats://usage`
Overall usage statistics across all models (JSON format).

### `config://providers`
Configuration status of all providers (JSON format).

## 💡 Usage Examples

### Using with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "ai-model-manager": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/ai-model-manager-mcp",
      "env": {
        "OPENAI_API_KEY": "your-key",
        "ANTHROPIC_API_KEY": "your-key"
      }
    }
  }
}
```

### Using with Other MCP Clients

The server uses stdio transport and can be integrated with any MCP-compatible client.

## 🏗️ Architecture

```
ai-model-manager-mcp/
├── src/
│   ├── models/          # Base model interfaces
│   ├── providers/       # Provider implementations
│   ├── storage/         # Database and configuration
│   ├── routing/         # Smart routing logic (future)
│   ├── utils/           # Utilities (future)
│   └── server.py        # Main MCP server
├── config/
│   └── models.json      # Model definitions
├── tests/               # Test suite
└── data/                # Database storage (created at runtime)
```

## 🔐 Security Notes

- API keys are stored in environment variables
- Database stores usage statistics locally
- In production, consider encrypting stored API keys
- Never commit `.env` file to version control

## 📊 Cost Tracking

The server automatically tracks:
- Token usage (input/output)
- Cost per request
- Latency metrics
- Provider performance

Access statistics via:
- `get_usage_stats` tool
- `stats://usage` resource
- Direct database queries

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
ruff check src/
```

### Type Checking

```bash
mypy src/
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional provider integrations
- Smart routing implementation
- Enhanced cost optimization
- Model performance benchmarking
- UI/dashboard for statistics

## 📝 License

MIT License - feel free to use in your projects!

## 🐛 Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# macOS: Restart Ollama app
# Linux: systemctl restart ollama
```

### API Key Issues
- Verify keys are correctly set in `.env`
- Check key permissions and quotas
- Ensure no extra spaces in key values

### Database Issues
```bash
# Reset database
rm -rf data/
# Server will recreate on next run
```

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review provider documentation
- Open an issue on GitHub

## 🎯 Roadmap

- [ ] Smart routing based on task complexity
- [ ] Model performance benchmarking
- [ ] Cost optimization recommendations
- [ ] Web dashboard for statistics
- [ ] Support for more providers (Cohere, Together AI)
- [ ] Fine-tuning workflow management
- [ ] Model evaluation tools

---

Built with ❤️ using the Model Context Protocol