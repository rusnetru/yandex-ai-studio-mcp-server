---
name: yandex-ai-studio
description: "Создание AI-агентов и бизнес-сервисов на Yandex AI Studio (YandexGPT, YandexART, SpeechKit) через локальный MCP-сервер. Интеграция агентов с CRM (amoCRM, Bitrix24, RetailCRM) для малого бизнеса РФ."
version: 1.0.0
---

# Yandex AI Studio: агенты и CRM-интеграция

## Контекст

Локальный MCP-сервер находится в `D:/MSP Servers/Yandex AI Studio MCP Server/server.py`. Он подключается к Hermes через stdio и предоставляет 21 инструмент для работы с Yandex Cloud AI Studio и CRM (amoCRM, Bitrix24, RetailCRM).

Агент может:
- Создавать AI-агентов под бизнес-задачи (поддержка, продажи, обработка заявок)
- Интегрировать агентов с CRM (amoCRM, Bitrix24, RetailCRM) через function calling
- Генерировать изображения, распознавать/синтезировать речь, строить поисковые индексы

---

## Часть 1: Создание AI-агентов

### Инструменты для работы с агентами

| Инструмент MCP | Назначение |
|---|---|
| `mcp_yandex_ai_studio_create_agent` | Создать конфигурацию агента (имя, промпт, модель, инструменты) |
| `mcp_yandex_ai_studio_run_agent` | Запустить агента с задачей (многошаговый цикл с function calling) |
| `mcp_yandex_ai_studio_list_agents` | Список созданных агентов |
| `mcp_yandex_ai_studio_chat` | Прямой чат с YandexGPT |
| `mcp_yandex_ai_studio_completion` | Текстовая генерация |
| `mcp_yandex_ai_studio_generate_image` | YandexART |
| `mcp_yandex_ai_studio_speech_to_text` | Распознавание речи |
| `mcp_yandex_ai_studio_text_to_speech` | Синтез речи |
| `mcp_yandex_ai_studio_get_embeddings` | Векторные эмбеддинги |
| `mcp_yandex_ai_studio_classify_text` | Классификация текста |
| `mcp_yandex_ai_studio_list_models` | Список моделей |
| `mcp_yandex_ai_studio_create_search_index` | Создать поисковый индекс |
| `mcp_yandex_ai_studio_search_in_index` | Поиск по индексу |
| `mcp_yandex_ai_studio_create_amocrm_lead` | Создать сделку в amoCRM |
| `mcp_yandex_ai_studio_find_amocrm_contact` | Найти контакт в amoCRM |
| `mcp_yandex_ai_studio_create_amocrm_task` | Создать задачу в amoCRM |
| `mcp_yandex_ai_studio_create_bitrix_lead` | Создать лид в Bitrix24 |
| `mcp_yandex_ai_studio_create_bitrix_deal` | Создать сделку в Bitrix24 |
| `mcp_yandex_ai_studio_search_bitrix_contacts` | Поиск контактов в Bitrix24 |
| `mcp_yandex_ai_studio_create_retailcrm_order` | Создать заказ в RetailCRM |
| `mcp_yandex_ai_studio_search_retailcrm_orders` | Найти заказы клиента в RetailCRM |

### Workflow создания агента

**Шаг 1: Определить бизнес-задачу**

Выяснить у Андрея:
- Что должен делать агент? (обработка заявок, ответы клиентам, квалификация лидов)
- Какие данные/системы ему нужны? (CRM, база знаний, сайт)
- Tone of voice, ограничения

**Шаг 2: Создать агента через create_agent**

```
mcp_yandex_ai_studio_create_agent(
    name="SupportBot",
    system_prompt="Ты — агент технической поддержки интернет-магазина...",
    model="yandexgpt",
    temperature=0.3,
    max_tokens=1500,
    tools_config=[...]
)
```

Агент сохраняется в `D:/MSP Servers/Yandex AI Studio MCP Server/agents/{agent_id}.json`

**Шаг 3: Протестировать агента**

```
mcp_yandex_ai_studio_run_agent(
    agent_id="SupportBot_abc123",
    task="Клиент: не могу войти в личный кабинет, пишет 'неверный пароль'"
)
```

**Шаг 4: Итеративно улучшить**

Если агент отвечает неудовлетворительно — скорректировать system_prompt, temperature, tools_config и пересоздать.

### Шаблоны системных промптов

#### Агент техподдержки
```
Ты — агент технической поддержки компании [НАЗВАНИЕ].
Правила:
1. Отвечай вежливо, по делу, без воды
2. Если проблема известна — дай пошаговую инструкцию
3. Если проблема требует эскалации — собери данные: имя, email, описание проблемы, скриншоты
4. Не придумывай функции, которых нет в продукте
5. Если клиент агрессивен — сохраняй спокойствие, предложи соединить с живым оператором
```

#### Агент квалификации лидов (для CRM)
```
Ты — агент квалификации входящих заявок.
Твоя задача: из разговора с клиентом извлечь и структурировать:
- Имя, компания, телефон, email
- Источник заявки (сайт, звонок, мессенджер)
- Бюджет (ориентировочный)
- Срочность (высокая/средняя/низкая)
- Категория запроса (из списка: ...)
- Краткое описание потребности

Верни результат в JSON для создания сделки в CRM.
```

#### Агент-консультант по продуктам
```
Ты — консультант интернет-магазина [НАЗВАНИЕ].
Твои знания: [ОПИСАНИЕ КАТАЛОГА, ЦЕНЫ, АКЦИИ]
Правила:
1. Помоги клиенту подобрать товар под его задачу
2. Сравнивай характеристики честно, указывай плюсы и минусы
3. Предлагай сопутствующие товары (но не навязчиво)
4. Если товара нет в наличии — предложи аналог
5. Завершай диалог призывом к действию (оформить заказ, позвонить)
```

---

## Часть 2: Интеграция с CRM для малого бизнеса

### Поддерживаемые CRM

| CRM | API | Аутентификация | Ключевые методы |
|---|---|---|---|
| **amoCRM** | REST API v4 (JSON) | OAuth 2.0 (долгосрочный токен) | POST /api/v4/leads, /api/v4/contacts, /api/v4/companies, /api/v4/tasks |
| **Bitrix24** | REST API | Webhook-URL (токен в URL) | crm.lead.add, crm.deal.add, crm.contact.add, crm.company.add, crm.activity.add |
| **RetailCRM** | REST API v5 | API-ключ в заголовке X-Api-Key | /api/v5/customers, /api/v5/orders |

### Архитектуры интеграции

#### Паттерн A: Agent → MCP → YandexGPT function calling → CRM API

Прямая интеграция: агент через function calling дёргает CRM API.

```
Пользователь → Hermes Agent → MCP Yandex AI Studio → create_agent(tools=[CRM functions])
                                                      → run_agent(task)
                                                        → YandexGPT с function calling
                                                          → POST /api/v4/leads (amoCRM)
```

**Плюсы**: просто, быстро, без доп. инфраструктуры
**Минусы**: агент должен иметь прямой доступ к CRM API

#### Паттерн B: CRM Webhook → Cloud Function → Agent

Обратная интеграция: CRM шлёт webhook при событии, облачная функция обрабатывает.

```
Событие в CRM (новая заявка) → Webhook → Yandex Cloud Function → YandexGPT → ответ → CRM API (комментарий/задача)
```

**Плюсы**: реакция на события CRM в реальном времени
**Минусы**: нужна облачная инфраструктура Yandex Cloud

#### Паттерн C: Agent как прослойка (MCP-интеграция)

Локальный Python-скрипт слушает CRM webhook, агент обрабатывает.

```
CRM Webhook → локальный Flask/FastAPI эндпоинт → MCP инструмент → YandexGPT → CRM API
```

**Плюсы**: полный контроль, можно запускать локально
**Минусы**: нужен статический IP/webhook-приёмник

### Шаблоны function calling для CRM

#### amoCRM: создание сделки

```json
{
  "type": "function",
  "function": {
    "name": "create_amocrm_lead",
    "description": "Создать сделку в amoCRM",
    "parameters": {
      "type": "object",
      "properties": {
        "name": {"type": "string", "description": "Название сделки"},
        "price": {"type": "number", "description": "Бюджет сделки"},
        "contact_name": {"type": "string"},
        "contact_phone": {"type": "string"},
        "contact_email": {"type": "string"}
      },
      "required": ["name"]
    }
  }
}
```

**Реализация**: MCP-инструмент выполняет POST на `https://{subdomain}.amocrm.ru/api/v4/leads` с заголовком `Authorization: Bearer {access_token}` и телом `[{name: ..., price: ..., _embedded: {contacts: [...]}}]`

#### amoCRM: поиск контакта

```json
{
  "type": "function",
  "function": {
    "name": "find_amocrm_contact",
    "description": "Найти контакт в amoCRM по телефону или email",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "Телефон или email для поиска"}
      },
      "required": ["query"]
    }
  }
}
```

**Реализация**: GET `https://{subdomain}.amocrm.ru/api/v4/contacts?query={query}`

#### Bitrix24: создание сделки

```json
{
  "type": "function",
  "function": {
    "name": "create_bitrix_deal",
    "description": "Создать сделку в Bitrix24 CRM",
    "parameters": {
      "type": "object",
      "properties": {
        "title": {"type": "string", "description": "Название сделки"},
        "opportunity": {"type": "number", "description": "Сумма"},
        "contact_name": {"type": "string"},
        "contact_phone": {"type": "string"},
        "comments": {"type": "string"}
      },
      "required": ["title"]
    }
  }
}
```

**Реализация**: POST `https://{domain}/rest/{user_id}/{webhook_token}/crm.deal.add` с полями `fields[TITLE]`, `fields[OPPORTUNITY]` и т.д.

#### Bitrix24: создание лида

```json
{
  "type": "function",
  "function": {
    "name": "create_bitrix_lead",
    "description": "Создать лид в Bitrix24 CRM",
    "parameters": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "name": {"type": "string"},
        "phone": {"type": "string"},
        "email": {"type": "string"},
        "source_description": {"type": "string"}
      },
      "required": ["title"]
    }
  }
}
```

#### RetailCRM: создание заказа

```json
{
  "type": "function",
  "function": {
    "name": "create_retailcrm_order",
    "description": "Создать заказ в RetailCRM",
    "parameters": {
      "type": "object",
      "properties": {
        "customer_name": {"type": "string"},
        "customer_phone": {"type": "string"},
        "customer_email": {"type": "string"},
        "items": {"type": "array", "items": {"type": "object", "properties": {"product_name": {"type": "string"}, "quantity": {"type": "number"}, "price": {"type": "number"}}}},
        "total": {"type": "number"}
      },
      "required": ["customer_phone"]
    }
  }
}
```

### CRM-функции уже реализованы — они работают "из коробки"

Эти функции больше не шаблон — они реализованы в `crm_tools.py` и зарегистрированы в `server.py` как:

1. **Прямые MCP-инструменты** — `create_amocrm_lead`, `find_amocrm_contact`, `create_amocrm_task`,
   `create_bitrix_lead`, `create_bitrix_deal`, `search_bitrix_contacts`,
   `create_retailcrm_order`, `search_retailcrm_orders`. Любой агент может вызвать их напрямую.
2. **Исполняемые function-calling инструменты внутри `run_agent`** — через `TOOL_REGISTRY` в
   `server.py`. Если в `tools_config` агента есть инструмент с именем из реестра, `run_agent`
   реально выполнит его (HTTP-запрос к CRM) и передаст результат модели — без участия MCP-хоста.

Нужно только заполнить соответствующие переменные в `.env` (`AMOCRM_*`, `BITRIX24_WEBHOOK`,
`RETAILCRM_*`) — без них вызов вернёт ошибку, но остальные инструменты сервера продолжат работать.

Если нужен метод CRM, которого ещё нет в `crm_tools.py` — добавьте туда функцию по аналогии
с существующими и зарегистрируйте её в `TOOL_REGISTRY` и как `@mcp.tool()` в `server.py`.

### Интеграция через Yandex Cloud Functions (Паттерн B)

Для production-интеграции CRM + AI Studio:

```python
# Облачная функция в Yandex Cloud (обработчик webhook из CRM)
import json
import requests

def handler(event, context):
    body = json.loads(event["body"])

    # 1. Извлекаем данные из webhook CRM
    lead_data = extract_lead_from_webhook(body)

    # 2. Вызываем YandexGPT для обработки
    ai_response = call_yandex_gpt(
        system_prompt="Ты — агент квалификации лидов...",
        user_message=json.dumps(lead_data, ensure_ascii=False)
    )

    # 3. Обновляем сделку в CRM результатом AI
    update_crm_lead(lead_data["id"], ai_response)

    return {"statusCode": 200, "body": "ok"}
```

---

## Часть 3: Типовые бизнес-сценарии

### Сценарий 1: Автоответчик для интернет-магазина

```
Клиент пишет в чат → MCP run_agent → YandexGPT анализирует вопрос →
  ├─ "Где заказ?" → запрос к CRM (RetailCRM/amoCRM API) → ответ с трек-номером
  ├─ "Хочу купить X" → поиск по каталогу (search_index) → консультация → создание заказа в CRM
  ├─ "Вернуть товар" → инструкция по возврату + создание задачи в CRM на менеджера
  └─ Сложный вопрос → эскалация на живого оператора (задача в CRM)
```

**Реализация**: create_agent с tools_config = [search_index, create_order, track_order, create_task]

### Сценарий 2: Квалификация входящих заявок

```
Заявка с сайта (webhook) → run_agent(agent_id="LeadQualifier")
  → классификация заявки (classify_text)
  → извлечение контактов (chat с function calling)
  → создание сделки в CRM
  → назначение ответственного менеджера
  → уведомление в Telegram
```

### Сценарий 3: Голосовой помощник для клиники

```
Звонок → SpeechKit STT → run_agent(agent_id="ClinicBot")
  → анализ запроса (chat)
  → проверка расписания (CRM API)
  → запись на приём (CRM API)
  → SpeechKit TTS → ответ голосом
```

### Сценарий 4: AI-конвейер обработки документов

```
Документ (PDF/скан) → распознавание (Vision/SpeechKit) → извлечение сущностей (completion)
  → создание записи в CRM → привязка к сделке → уведомление менеджера
```

---

## Часть 4: Добавление CRM-функций в MCP-сервер

### Пошаговый план расширения сервера

1. **Получить доступы к CRM** (спросить у Андрея):
   - amoCRM: субдомен + долгосрочный токен
   - Bitrix24: домен + webhook-токен
   - RetailCRM: домен + API-ключ

2. **Добавить ключи в `.env`** MCP-сервера:
   ```env
   AMOCRM_SUBDOMAIN=yourcompany
   AMOCRM_ACCESS_TOKEN=...
   BITRIX24_WEBHOOK=https://yourcompany.bitrix24.ru/rest/1/token/
   RETAILCRM_DOMAIN=yourcompany
   RETAILCRM_API_KEY=...
   ```

3. **Добавить инструменты в server.py** — функции `create_amocrm_lead`, `find_amocrm_contact`, `create_bitrix_deal` и т.д.

4. **Обновить create_agent** — поддержка CRM-функций в tools_config.

5. **Протестировать** сквозной сценарий: создать агента → запустить с задачей → проверить сделку в CRM.

---

## Важные замечания

- **MCP-сервер работает локально**, не требует облачной инфраструктуры Yandex Cloud, кроме API-ключей AI Studio
- **Агенты сохраняются** в `D:/MSP Servers/Yandex AI Studio MCP Server/agents/` — переиспользуются между сессиями
- **Function calling** YandexGPT поддерживает OpenAI-совместимый формат инструментов
- **amoCRM** использует OAuth 2.0 с refresh-токенами — долгосрочный токен получается один раз и живёт 3 месяца
- **Bitrix24** проще для начала: webhook-токен генерируется в админке и не истекает
- **RetailCRM** использует X-Api-Key в заголовке — самый простой в интеграции

## Порядок действий при создании нового бизнес-решения

1. Понять бизнес-процесс (запросить у Андрея детали)
2. Выбрать CRM и паттерн интеграции
3. Создать агента через `create_agent` с system_prompt и tools_config
4. При необходимости расширить MCP-сервер новыми CRM-функциями
5. Протестировать через `run_agent`
6. Задокументировать решение (README в папке агента)
