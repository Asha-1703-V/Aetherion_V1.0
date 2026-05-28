# 🌀 Aetherion - Enterprise AI Orchestration Platform

**Production-ready, self-hosted AI workflow engine с поддержкой LLM, очередей и веб-интерфейса**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-24.0+-blue.svg)](https://www.docker.com/)

## ✨ Features

- 🚀 **Zero-config startup** — `docker-compose up` и вы в продакшене
- 🤖 **Multi-LLM support** — OpenRouter (DeepSeek/Gemini), легко расширяется под OpenAI/Anthropic
- 🌐 **Бесплатный встроенный переводчик** — Google Translate API (EN↔RU)
- 📊 **Real-time логи** — через WebSocket (в разработке)
- 💰 **Cost tracking** — отслеживание затрат на каждый workflow run
- 🔧 **5 готовых воркфлоу** — калькулятор, AI чат, парсинг сайтов, ревью кода, переводчик
- 📈 **Встроенный дашборд** — метрики, история запусков, быстрые примеры
- 🐳 **Полный Docker Compose** — PostgreSQL, Redis, MinIO, Gateway, Worker, Frontend, Nginx

## 🚀 Quick Start

### Требования
- Docker Desktop 24.0+
- Git
- 4GB RAM (рекомендуется 8GB)

### Установка и запуск

```bash
# Клонируйте репозиторий
git clone https://github.com/Asha-1703-V/Aetherion-Platform.git
cd Aetherion-Platform

# Создайте файл с секретами (опционально, для AI)
cp .env.example .env
# Отредактируйте .env и добавьте ваш OpenRouter API ключ

# Запустите все сервисы
docker-compose up -d

# Откройте в браузере
open http://localhost
```

## Доступные endpoints
| Сервис                 | URL                                  | Описание                                     |
|------------------------|--------------------------------------|----------------------------------------------|
| **Frontend Dashboard** | http://localhost                     | Веб-интерфейс для управления workflow        |
| **API Gateway**        | http://localhost:8000                | REST API для выполнения запросов             |
| **Swagger UI**         | http://localhost:8000/docs           | Интерактивная документация API               |
| **API Metrics**        | http://localhost:8000/api/v1/metrics | Метрики: количество запусков, ошибки, затраты|
| **MinIO Console**      | http://localhost:9001                | Хранилище артефактов (логи, файлы)           |

## 🏗 Architecture
```
┌────────────┐     ┌─────────────┐     ┌──────────┐     ┌──────────────┐
│  Browser   │────▶│   Nginx     │────▶│  Redis   │────▶│ Orchestrator │
│  :3000     │     │  :80        │     │ Streams  │     │   Worker     │
└────────────┘     └─────┬───────┘     └──────────┘     └──────┬───────┘
                         │                                     │
                    ┌────▼───────┐                        ┌────▼───────┐
                    │  Gateway   │                        │   LLMs     │
                    │ (FastAPI)  │                        │  & Tools   │
                    └────┬───────┘                        └────────────┘
                         │
                    ┌────▼───────┐
                    │ Postgres   │
                    │  & MinIO   │
                    └────────────┘
```

### 🔧 Development

Запуск в режиме разработки
```bash
# Запустить только бэкенд в Docker
docker-compose up -d postgres redis gateway orchestrator minio

# Запустить frontend на хосте (с hot-reload)
cd frontend
npm install
npm run dev
```

Полезные команды
```bash
# Пересобрать все сервисы
docker-compose build --no-cache

# Посмотреть логи
docker-compose logs -f

# Перезапустить конкретный сервис
docker-compose restart orchestrator

# Остановить всё
docker-compose down

# Остановить и удалить все данные
docker-compose down -v
```

### 🔐 Настройка API ключей
```
Для работы AI чата и code review нужен API ключ OpenRouter:

- Зарегистрируйтесь на OpenRouter

- Получите API ключ в разделе "Keys"

- Создайте файл .env в корне проекта:

OPENROUTER_API_KEY=sk-or-v1-ваш_ключ

- Перезапустите orchestrator
```


## 📝 License
Distributed under the MIT License. See LICENSE for more information.

## 📧 Contact
Автор: Asha-1703-V
@Way_Asha