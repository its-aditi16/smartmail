# Mistral Model Directory

This directory is intended to store the Mistral model files for the LangChain agent.

## Usage

The Mistral model is used through the Ollama integration in LangChain. The model files will be managed by Ollama.

## Setup

1. Install Ollama from [https://ollama.ai/](https://ollama.ai/)
2. Pull the Mistral model:
   ```bash
   ollama pull mistral
   ```

## Configuration

The model is configured in `agent.py` with the following settings:

```python
agent = initialize_agent(
    tools=tools,
    llm=OllamaLLM(),
    verbose=True
)
```

You can customize the model settings as needed. 