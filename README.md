# Yandex AI Studio MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)

**MCP-сервер для полного доступа AI-агентов к Yandex Cloud AI Studio: языковые модели, генерация изображений, синтез речи, эмбеддинги, классификация, CRM-автоматизация.**

AI-агент через стандартный Model Context Protocol получает более 20 инструментов — от чата с YandexGPT до создания сделок в Bitrix24, amoCRM и RetailCRM. Плюс уникальная возможность: агент может **создавать и запускать других AI-агентов** для бизнес-задач.

## Возможности

### AI & ML

| Инструмент | API | Назначение |
|-----------|-----|-----------|
| `chat` | YandexGPT Pro/Lite | OpenAI-совместимый чат с function calling |
| `completion` | YandexGPT | Простая текстовая генерация |
| `generate_image` | YandexART | Генерация изображений (1024×1024) |
| `speech_to_text` | SpeechKit STT | Распознавание речи (ru-RU, en-US, kk-KK, tr-TR) |
| `text_to_speech` | SpeechKit TTS | Синтез речи (oksana, jane, omazh, zahar, ermil) |
| `get_embeddings` | Embeddings API | Векторные эмбеддинги для поиска/RAG |
| `classify_text` | YandexGPT Classifier | Классификация: sentiment, topic, intent |
| `list_models` | — | Список доступных моделей |

### AI-агенты (ключевая фича)

| Инструмент | Описание |
|-----------|----------|
| `create_agent` | Создать AI-агента с системным промптом и инструментами |
| `run_agent` | Запустить агента с задачей (многошаговый function calling) |
| `list_agents` | Список созданных агентов |

Агенты сохраняются в `./agents/` и переиспользуются. `run_agent` реально выполняет CRM-вызовы — не эмулирует.

### Поисковые индексы

| Инструмент | Описание |
|-----------|----------|
| `create_search_index` | Создать индекс (текстовый, векторный, гибридный) |
| `search_in_index` | Поиск по индексу |

### CRM-автоматизация

| Инструмент | CRM | Операция |
|-----------|-----|----------|
| `create_amocrm_lead` | amoCRM | Создать сделку с контактом |
| `find_amocrm_contact` | amoCRM | Поиск контакта |
| `create_amocrm_task` | amoCRM | Создать задачу |
| `create_bitrix_lead` | Bitrix24 | Создать лид |
| `create_bitrix_deal` | Bitrix24 | Создать сделку |
| `search_bitrix_contacts` | Bitrix24 | Поиск контактов |
| `create_retailcrm_order` | RetailCRM | Создать заказ |
| `search_retailcrm_orders` | RetailCRM | Найти заказы клиента |

CRM-инструменты опциональны — работают только с соответствующими ключами в `.env`.

## Быстрый старт

### 1. Установка

```bash
git clone https://github.com/rusnetru/yandex-ai-studio-mcp-server.git
cd yandex-ai-studio-mcp-server
pip install -r requirements.txt
```

### 2. Конфигурация

Создайте `.env`:

```env
YANDEX_FOLDER_ID=b1gxxxxxxxxxxxxxxxxxxxxxxxxx
YANDEX_API_KEY=AQVNxx...

# Опционально — CRM
AMOCRM_SUBDOMAIN=yourcompany
AMOCRM_ACCESS_TOKEN=...
BITRIX24_WEBHOOK=https://your.bitrix24.ru/rest/1/token/
RETAILCRM_DOMAIN=yourcompany
RETAILCRM_API_KEY=...
```

### 3. Подключение к Claude Desktop

```json
{
  "mcpServers": {
    "yandex-ai-studio": {
      "command": "python",
      "args": ["D:/MSP Servers/Yandex AI Studio MCP Server/server.py"],
      "env": {
        "YANDEX_FOLDER_ID": "b1g...",
        "YANDEX_API_KEY": "AQVN..."
      }
    }
  }
}
```

### 4. Подключение к Hermes Agent

```yaml
mcp_servers:
  yandex-ai-studio:
    command: "python"
    args: ["D:/MSP Servers/Yandex AI Studio MCP Server/server.py"]
    env:
      YANDEX_FOLDER_ID: "b1g..."
      YANDEX_API_KEY: "AQVN..."
    timeout: 120
```

## Пример: AI-агент техподдержки

```python
# Агент создаёт другого агента:
→ create_agent(
    name="SupportBot",
    system_prompt="Ты агент техподдержки. При проблемах с заказом — ищи в RetailCRM.",
    tools=["search_retailcrm_orders"]
)

# Запускает с задачей:
→ run_agent(
    agent_id="SupportBot_abc123",
    task="Клиент +79991234567 не получил заказ #12345. Найди заказ и объясни статус."
)

# Агент сам вызывает CRM, находит заказ, формулирует ответ.
```

## Модели YandexGPT

| Модель | Контекст | Назначение |
|--------|---------|-----------|
| `yandexgpt` | 8K | Основная Pro-модель |
| `yandexgpt-lite` | 8K | Быстрая/лёгкая |
| `yandexgpt-32k` | 32K | Длинные документы |

## Требования

- Python 3.11+
- Yandex Cloud аккаунт + API-ключ (или IAM-токен)
- Для CRM: соответствующие учётные записи

## Лицензия

MIT
