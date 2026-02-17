# 🚀 Quick Start Guide

Get up and running with the AI Model Manager MCP Server in 5 minutes!

## Step 1: Install Dependencies

```bash
cd ai-model-manager-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys (at minimum, add one provider):

```env
# For local models only (free!)
OLLAMA_HOST=http://localhost:11434

# Or add cloud providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Step 3: Install Ollama (Optional but Recommended)

For free local models:

```bash
# Install Ollama from https://ollama.ai
# Then pull a model:
ollama pull llama3.2
```

## Step 4: Test the Server

```bash
# Run the server
python -m src.server
```

## Step 5: Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-models": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/full/path/to/ai-model-manager-mcp"
    }
  }
}
```

Restart Claude Desktop and you're ready!

## 🎯 Try These Commands in Claude

1. **List available models:**
   > "List all available AI models"

2. **Generate with a local model:**
   > "Use the llama3.2 model from ollama to explain quantum computing"

3. **Compare models:**
   > "Compare how llama3.2 and gpt-4o-mini respond to: Write a haiku about coding"

4. **Check costs:**
   > "Show me my usage statistics"

## 💡 Tips

- Start with Ollama for free local models
- Add cloud providers as needed
- Use `compare_models` to find the best model for your tasks
- Check `stats://usage` resource for cost tracking

## 🆘 Need Help?

- Ollama not working? Check if it's running: `ollama list`
- API errors? Verify your keys in `.env`
- See full README.md for detailed documentation

Happy model managing! 🎉