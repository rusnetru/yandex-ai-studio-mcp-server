# Yandex AI Studio MCP Server

Локальный MCP-сервер для работы AI-агентов с Yandex Cloud AI Studio.

## Возможности

| Категория       | Инструменты                            | API Yandex Cloud           |
|-----------------|----------------------------------------|----------------------------|
| Чат и генерация | `chat`, `completion`                   | YandexGPT Pro/Lite         |
| Изображения     | `generate_image`                       | YandexART                  |
| Речь            | `speech_to_text`, `text_to_speech`     | SpeechKit STT/TTS          |
| Эмбеддинги      | `get_embeddings`                       | Embeddings API             |
| Классификация   | `classify_text`                        | YandexGPT Classifier       |
| Поисковые индексы | `create_search_index`, `search_in_index` | Search Index API         |
| **AI-агенты**   | `create_agent`, `run_agent`, `list_agents` | YandexGPT + Function Calling |

## Ключевая фича: создание AI-агентов

Сервер позволяет агенту создавать других AI-агентов для бизнес-задач:

1. **`create_agent`** — создаёт конфигурацию агента (имя, системный промпт, модель, инструменты)
2. **`run_agent`** — запускает агента с задачей (многошаговый цикл с function calling)
3. **`list_agents`** — показывает всех созданных агентов

Агенты сохраняются в `./agents/` и переиспользуются между сессиями.

### Пример: агент поддержки

```
→ create_agent(name="Support", system_prompt="Ты агент техподдержки...", tools=[...])
→ run_agent(agent_id="Support_abc123", task="Пользователь не может войти в систему")
```

## Быстрый старт

### 1. Установка

```bash
cd "D:\MSP Servers\Yandex AI Studio MCP Server"
pip install -r requirements.txt
```

### 2. Конфигурация

Создайте `.env` на основе `.env.example`:

```env
YANDEX_FOLDER_ID=b1gxxxxxxxxxxxxxxxxxxxxxxxxx
YANDEX_API_KEY=AQVNxx...
```

Альтернативно — IAM-токен из `yc iam create-token`:

```env
YANDEX_FOLDER_ID=b1gxxxxxxxxxxxxxxxxxxxxxxxxx
YANDEX_IAM_TOKEN=t1.9euelZ...
```

### 3. Подключение к Hermes Agent

Добавьте в `~/.hermes/config.yaml` в секцию `mcp_servers`:

```yaml
mcp_servers:
  yandex-ai-studio:
    command: "python"
    args: ["D:/MSP Servers/Yandex AI Studio MCP Server/server.py"]
    env:
      YANDEX_FOLDER_ID: "b1gxxxxxxxxxxxxxxxxxxxxxxxxx"
      YANDEX_API_KEY: "AQVNxx..."
    timeout: 120
```

### 4. Проверка

Запустите сервер напрямую (для отладки):

```bash
cd "D:\MSP Servers\Yandex AI Studio MCP Server"
python server.py
```

Или через MCP Inspector:

```bash
npx @anthropic-ai/mcp-inspector python "D:/MSP Servers/Yandex AI Studio MCP Server/server.py"
```

## Инструменты

| Инструмент          | Назначение                                 |
|---------------------|--------------------------------------------|
| `chat`              | OpenAI-совместимый чат с YandexGPT         |
| `completion`        | Простая текстовая генерация                |
| `generate_image`    | Генерация изображений (YandexART)          |
| `speech_to_text`    | Распознавание речи (SpeechKit STT)         |
| `text_to_speech`    | Синтез речи (SpeechKit TTS)                |
| `get_embeddings`    | Векторные эмбеддинги                       |
| `classify_text`     | Классификация текста                       |
| `list_models`       | Список доступных моделей                   |
| `create_agent`      | Создать AI-агента                          |
| `run_agent`         | Запустить AI-агента с задачей              |
| `list_agents`       | Список созданных агентов                   |
| `create_search_index` | Создать поисковый индекс                |
| `search_in_index`   | Поиск по индексу                           |

## Модели

- **yandexgpt** — основная модель (Pro, 8K контекст)
- **yandexgpt-lite** — лёгкая модель
- **yandexgpt-32k** — расширенный контекст 32K
- **yandex-art** — генерация изображений

## Лицензия

MIT
