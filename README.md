# 🌀 Aetherion - Enterprise AI Orchestration Platform

**Production-ready, self-hosted AI workflow engine**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🚀 **Zero-config startup** - `docker-compose up` and you're live
- 🤖 **Multi-LLM support** (OpenAI, with easy extension for Anthropic/Local)
- 📊 **Real-time logs** via WebSocket
- 💰 **Cost tracking** per workflow run
- 🔧 **Extensible tools** (HTTP, Calculator, Code Review, Custom)
- 📈 **Metrics dashboard** built-in
- 🐳 **Full Docker Compose** setup for production

## 🚀 Quick Start

```bash
# Clone and enter directory
git clone https://github.com/yourcompany/aetherion.git
cd aetherion

# Start everything (Postgres, Redis, MinIO, Gateway, Worker, Frontend)
docker-compose up -d

# Optional: Set OpenAI API key for real AI
echo "OPENAI_API_KEY=sk-your-key" > .env
docker-compose restart orchestrator

# Open in browser
open http://localhost:3000
```

## 📡 API Usage
```bash
# Execute AI Chat workflow
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "ai_chat",
    "payload": {"prompt": "Hello AI!"},
    "async_mode": false
  }'

# Get result by ID
curl http://localhost:8000/api/v1/result/{run_id}

# Get metrics
curl http://localhost:8000/api/v1/metrics
```

## 🏗 Architecture
```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌────────────┐
│ Browser │────▶│ Gateway │────▶│  Redis   │────▶│Orchestrator│
└─────────┘     │(FastAPI)│     │ Streams  │     │   Worker   │
                └────┬────┘     └──────────┘     └─────┬──────┘
                     │                                 │
                ┌────▼────┐                      ┌─────▼─────┐
                │Postgres │                      │   LLMs    │
                └─────────┘                      │  & Tools  │
                                                 └───────────┘
```

## 🛠 Available Workflows
```
Workflow	Description	Example Payload
ai_chat	Conversational AI	{"prompt": "Hello"}
fetch_and_summarize	Web page summarizer	{"url": "https://example.com"}
calculator	Safe math evaluator	{"expression": "2+2*10"}
code_review	AI code analysis	{"code": "function add(a,b){return a+b}"}
```

## 📊 Monitoring
API Docs: http://localhost:8000/docs

Metrics: http://localhost:8000/api/v1/metrics

MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

UI — http://localhost:3000

## 🔧 Development
```bash
# Rebuild after changes
make build

# Restart all services
make restart

# View logs
make logs

# Run migrations manually
make migrate
```

## 🎯 Roadmap
Custom tool registration API

YAML-based workflow DAGs

Slack/Telegram integration

Kubernetes Helm chart

LangChain integration

## 📝 License
MIT - Use for any purpose, commercial or personal.