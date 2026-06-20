"""
Yandex AI Studio MCP Server
============================
Локальный MCP-сервер для работы с Yandex Cloud AI Studio (YandexGPT, YandexART,
SpeechKit, Embeddings, Function Calling).

Предоставляет инструменты агенту для:
- Генерации текста и чата (YandexGPT)
- Создания AI-агентов с системными промптами и инструментами
- Запуска агентов для решения бизнес-задач
- Генерации изображений (YandexART)
- Распознавания и синтеза речи (SpeechKit)
- Векторных эмбеддингов
- Классификации текста
- Управления поисковыми индексами

Транспорт: stdio (Model Context Protocol)
SDK: yandex-ai-studio-sdk

Конфигурация через .env в той же папке:
  YANDEX_FOLDER_ID — ID каталога Yandex Cloud (обязательно)
  YANDEX_API_KEY   — API-ключ (обязательно, если нет IAM-токена)
  YANDEX_IAM_TOKEN — IAM-токен (альтернатива API_KEY)
  YANDEX_MODEL     — модель по умолчанию (default: yandexgpt)
"""

import os
import sys
import json
import base64
import logging
from typing import Any
from pathlib import Path

# === Загрузка .env из папки сервера ===
from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent
load_dotenv(SERVER_DIR / ".env")

# === Инициализация SDK ===
from yandex_ai_studio_sdk import AIStudio

from mcp.server.fastmcp import FastMCP

# --- Logging ---
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [YandexAI-MCP] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("yandex-ai-mcp")

# --- MCP Server ---
mcp = FastMCP("Yandex AI Studio")
_sdk: AIStudio | None = None
_default_model: str = os.getenv("YANDEX_MODEL", "yandexgpt")

# ============================================================
#  SDK Factory
# ============================================================

def get_sdk() -> AIStudio:
    """Возвращает singleton SDK-клиента. При отсутствии ключей — ошибка."""
    global _sdk
    if _sdk is not None:
        return _sdk

    folder_id = os.getenv("YANDEX_FOLDER_ID", "").strip()
    api_key = os.getenv("YANDEX_API_KEY", "").strip()
    iam_token = os.getenv("YANDEX_IAM_TOKEN", "").strip()

    # Fallback: read from Андрей's key file if env is empty
    if not api_key:
        key_file = Path("D:/my_ai_agent/Yandex cloude api.txt")
        if key_file.exists():
            with open(key_file) as f:
                for line in f:
                    if "AQVN" in line:
                        api_key = line.strip().split()[-1]
                        logger.info("API key loaded from %s", key_file)
                        break

    if not folder_id:
        raise RuntimeError(
            "YANDEX_FOLDER_ID не задан. Создайте .env в папке сервера:\n"
            f"  {SERVER_DIR / '.env'}\n"
            "Скопируйте .env.example и заполните YANDEX_FOLDER_ID + YANDEX_API_KEY"
        )

    auth = api_key or iam_token or None
    if not auth:
        raise RuntimeError(
            "Нет ключа аутентификации. Задайте YANDEX_API_KEY или YANDEX_IAM_TOKEN в .env"
        )

    logger.info("Инициализация SDK: folder_id=%.8s...", folder_id)
    _sdk = AIStudio(folder_id=folder_id, auth=auth)
    return _sdk


# ============================================================
#  Helper: сериализация сложных объектов
# ============================================================

def _safe_json(obj: Any) -> str:
    """Безопасная сериализация в JSON."""
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except (TypeError, ValueError):
        return str(obj)


# ============================================================
#  MCP Tools
# ============================================================

@mcp.tool()
def chat(
    messages: list[dict[str, str]],
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    system_prompt: str = "",
    tools: list[dict] | None = None,
) -> str:
    """
    OpenAI-совместимый чат с YandexGPT. Поддерживает function calling.

    Args:
        messages: Список сообщений [{"role": "user"|"assistant"|"system", "content": "..."}]
        model: Модель (yandexgpt, yandexgpt-lite, etc.). По умолчанию yandexgpt.
        temperature: Температура генерации (0.0 — 1.0)
        max_tokens: Максимальное число токенов в ответе
        system_prompt: Системный промпт (добавляется как system message)
        tools: Список инструментов для function calling (OpenAI-совместимый формат)

    Returns:
        Ответ модели в JSON: {"content": "...", "tool_calls": [...]}
    """
    sdk = get_sdk()
    model_name = model or _default_model

    # Формируем сообщения
    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.extend(messages)

    try:
        chat_model = sdk.chat.completions

        kwargs = {
            "model": model_name,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        result = chat_model.create(**kwargs)
        choice = result.choices[0]
        msg = choice.message

        response = {"content": msg.content or "", "role": msg.role}
        if msg.tool_calls:
            response["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        return _safe_json(response)

    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def completion(
    prompt: str,
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Простая текстовая генерация (completion) через YandexGPT.

    Args:
        prompt: Текст запроса
        model: Модель (yandexgpt, yandexgpt-lite). По умолчанию yandexgpt.
        temperature: Температура (0.0 — 1.0)
        max_tokens: Максимум токенов

    Returns:
        Сгенерированный текст в JSON: {"text": "..."}
    """
    sdk = get_sdk()
    model_name = model or _default_model

    try:
        completion_model = sdk.models.completions(model_name)
        completion_model = completion_model.configure(
            temperature=temperature, max_tokens=max_tokens
        )
        result = completion_model.run(prompt)
        alternatives = [str(alt) for alt in result]
        return _safe_json({"text": alternatives[0] if alternatives else "", "alternatives": alternatives})
    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    style: str = "",
) -> str:
    """
    Генерация изображения через YandexART.

    Args:
        prompt: Текстовое описание изображения
        width: Ширина (кратно 64, макс 2048)
        height: Высота (кратно 64, макс 2048)
        style: Стиль (опционально): "default", "art", "photo", "digital"

    Returns:
        JSON с image_url (base64 data URL) или ошибкой
    """
    sdk = get_sdk()

    try:
        gen = sdk.models.image_generation("yandex-art")
        kwargs = {"prompt": prompt, "width": width, "height": height}
        if style:
            kwargs["style"] = style

        result = gen.run(**kwargs)
        if hasattr(result, "image") and result.image:
            img = result.image
            if isinstance(img, bytes):
                b64 = base64.b64encode(img).decode("utf-8")
                return _safe_json({"image_url": f"data:image/png;base64,{b64}", "status": "success"})
            return _safe_json({"image_url": str(img), "status": "success"})
        return _safe_json({"error": "Пустой результат от YandexART"})

    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def speech_to_text(
    audio_path: str,
    language: str = "ru-RU",
) -> str:
    """
    Распознавание речи через Yandex SpeechKit STT.

    Args:
        audio_path: Путь к аудиофайлу (локальный путь или URL)
        language: Язык ('ru-RU', 'en-US', 'kk-KK', 'tr-TR', 'de-DE', etc.)

    Returns:
        JSON: {"text": "распознанный текст..."} или ошибка
    """
    sdk = get_sdk()

    try:
        stt = sdk.speechkit.stt
        result = stt.recognize(audio=audio_path, language=language)
        return _safe_json({"text": result.text if hasattr(result, "text") else str(result)})
    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def text_to_speech(
    text: str,
    voice: str = "oksana",
    speed: float = 1.0,
    output_path: str = "",
    language: str = "ru-RU",
) -> str:
    """
    Синтез речи через Yandex SpeechKit TTS.

    Args:
        text: Текст для озвучивания
        voice: Голос (oksana, jane, omazh, zahar, ermil, etc.)
        speed: Скорость (0.1 — 3.0)
        output_path: Путь для сохранения аудио. Если не указан — сохраняется в папку сервера.
        language: Язык ('ru-RU', 'en-US', 'kk-KK', 'tr-TR', 'de-DE')

    Returns:
        JSON: {"audio_path": "путь к файлу", "format": "mp3"}
    """
    sdk = get_sdk()

    try:
        tts = sdk.speechkit.tts
        result = tts.synthesize(
            text=text, voice=voice, speed=speed, language=language
        )

        if output_path:
            filepath = output_path
        else:
            filepath = str(SERVER_DIR / f"tts_output_{hash(text) & 0xFFFF}.mp3")

        if hasattr(result, "audio") and result.audio:
            audio_data = result.audio
            if isinstance(audio_data, bytes):
                with open(filepath, "wb") as f:
                    f.write(audio_data)
            else:
                with open(filepath, "w") as f:
                    f.write(str(audio_data))
        else:
            with open(filepath, "wb") as f:
                f.write(result if isinstance(result, bytes) else str(result).encode())

        return _safe_json({"audio_path": filepath, "format": "mp3", "status": "success"})
    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def get_embeddings(
    texts: list[str],
    model: str = "embedding",
) -> str:
    """
    Получение векторных эмбеддингов для текстов.

    Args:
        texts: Список текстов для эмбеддинга
        model: Модель эмбеддингов (embedding — поисковая, embedding-doc — для документов)

    Returns:
        JSON: {"embeddings": [[float, ...], ...], "dimension": N}
    """
    sdk = get_sdk()

    try:
        emb = sdk.models.embeddings(model)
        result = emb.run(texts)

        embeddings = []
        for vec in result:
            if hasattr(vec, "embedding"):
                embeddings.append(vec.embedding)
            elif hasattr(vec, "vector"):
                embeddings.append(vec.vector)
            else:
                embeddings.append(list(vec) if hasattr(vec, "__iter__") else [])

        dimension = len(embeddings[0]) if embeddings else 0
        return _safe_json({"embeddings": embeddings, "dimension": dimension, "count": len(embeddings)})
    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def classify_text(
    text: str,
    task: str = "sentiment",
    model: str = "classifier",
) -> str:
    """
    Классификация текста через YandexGPT-классификаторы.

    Args:
        text: Текст для классификации
        task: Тип задачи: "sentiment", "topic", "intent", или свой кастомный
        model: Модель классификатора

    Returns:
        JSON: {"labels": [...], "scores": [...]}
    """
    sdk = get_sdk()

    try:
        classifier = sdk.models.classifiers(model)
        result = classifier.run(text=text, task=task)

        return _safe_json({
            "labels": getattr(result, "labels", []),
            "scores": getattr(result, "scores", []),
            "task": task,
            "raw": str(result),
        })
    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def list_models() -> str:
    """
    Список доступных моделей и их возможностей в AI Studio.

    Returns:
        JSON со списком моделей
    """
    return _safe_json({
        "chat_models": [
            {"name": "yandexgpt", "description": "YandexGPT Pro — основная модель, 8K контекст"},
            {"name": "yandexgpt-lite", "description": "YandexGPT Lite — лёгкая модель, 8K контекст"},
            {"name": "yandexgpt-32k", "description": "YandexGPT Pro 32K — расширенный контекст"},
        ],
        "image_models": [
            {"name": "yandex-art", "description": "YandexART — генерация изображений"},
        ],
        "embedding_models": [
            {"name": "embedding", "description": "Поисковые эмбеддинги (256-мерные)"},
            {"name": "embedding-doc", "description": "Эмбеддинги документов (1024-мерные)"},
        ],
        "classifier_models": [
            {"name": "classifier", "description": "YandexGPT-классификатор (sentiment, topic, intent)"},
        ],
        "speech_voices": [
            "oksana", "jane", "omazh", "zahar", "ermil", "alena", "filipp",
        ],
    })


# ============================================================
#  AGENT CREATION — ключевая фича
# ============================================================

@mcp.tool()
def create_agent(
    name: str,
    system_prompt: str,
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    tools_config: list[dict] | None = None,
) -> str:
    """
    Создаёт конфигурацию AI-агента, готового к запуску через run_agent.

    Агент — это модель YandexGPT с системным промптом и опциональным набором
    инструментов (function calling). После создания агента его можно запустить
    с конкретной задачей через инструмент run_agent.

    Args:
        name: Имя агента (например, "CustomerSupportBot", "CodeReviewAgent")
        system_prompt: Системный промпт — описывает роль, правила, tone of voice
        model: Модель (yandexgpt, yandexgpt-lite). По умолчанию yandexgpt.
        temperature: Температура (0.0 = точность, 1.0 = креативность)
        max_tokens: Максимальная длина ответа
        tools_config: Список инструментов в OpenAI function calling формате.
            Пример: [{"type": "function", "function": {"name": "search", "description": "...", "parameters": {...}}}]

    Returns:
        JSON с конфигурацией агента (сохрани agent_id для использования в run_agent)
    """
    sdk = get_sdk()
    model_name = model or _default_model

    # Сохраняем конфигурацию агента (в оперативной памяти и в файл)
    agent_id = f"{name}_{hash(system_prompt + model_name) & 0xFFFFFFFF:08x}"
    agent_config = {
        "agent_id": agent_id,
        "name": name,
        "system_prompt": system_prompt,
        "model": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tools": tools_config or [],
    }

    # Сохраняем конфигурацию в JSON-файл для персистентности
    agents_dir = SERVER_DIR / "agents"
    agents_dir.mkdir(exist_ok=True)
    config_path = agents_dir / f"{agent_id}.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(agent_config, f, ensure_ascii=False, indent=2)

    logger.info("Агент '%s' создан: %s", name, config_path)

    return _safe_json({
        "status": "created",
        "agent_id": agent_id,
        "name": name,
        "model": model_name,
        "config_path": str(config_path),
        "usage_hint": f"Используйте run_agent(agent_id='{agent_id}', task='ваша задача') для запуска",
    })


@mcp.tool()
def run_agent(
    agent_id: str,
    task: str,
    context: list[dict[str, str]] | None = None,
    max_steps: int = 10,
) -> str:
    """
    Запускает AI-агента (созданного через create_agent) для выполнения задачи.

    Агент получает задачу и выполняет её в многошаговом цикле:
    - Если у агента есть инструменты — он может вызывать их через function calling
    - Результаты инструментов подставляются в контекст
    - Цикл продолжается пока агент не даст финальный ответ или не достигнут max_steps

    Args:
        agent_id: ID агента (из create_agent или list_agents)
        task: Задача для агента
        context: Опциональный список предыдущих сообщений для сохранения контекста
        max_steps: Максимальное число шагов (для агентов с инструментами)

    Returns:
        JSON: {"agent_id": "...", "result": "финальный ответ", "steps": N, "history": [...]}
    """
    sdk = get_sdk()

    # Загружаем конфигурацию агента
    agents_dir = SERVER_DIR / "agents"
    config_path = agents_dir / f"{agent_id}.json"
    if not config_path.exists():
        return _safe_json({
            "error": f"Агент '{agent_id}' не найден. Доступные агенты в {agents_dir}",
            "available_agents": [f.stem for f in agents_dir.glob("*.json")],
        })

    with open(config_path, "r", encoding="utf-8") as f:
        agent_cfg = json.load(f)

    model_name = agent_cfg["model"]
    system_prompt = agent_cfg["system_prompt"]
    temperature = agent_cfg.get("temperature", 0.7)
    max_tokens = agent_cfg.get("max_tokens", 2000)
    tools = agent_cfg.get("tools", [])

    # Строим историю сообщений
    history = []
    if context:
        history.extend(context)
    history.append({"role": "user", "content": task})

    try:
        chat_model = sdk.chat.completions

        for step in range(max_steps):
            kwargs = {
                "model": model_name,
                "messages": history,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                kwargs["tools"] = tools

            result = chat_model.create(**kwargs)
            choice = result.choices[0]
            msg = choice.message

            # Сохраняем ответ в историю
            assistant_msg = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ]
            history.append(assistant_msg)

            # Если нет tool_calls — это финальный ответ
            if not msg.tool_calls:
                return _safe_json({
                    "agent_id": agent_id,
                    "agent_name": agent_cfg["name"],
                    "result": msg.content or "[нет текста]",
                    "steps": step + 1,
                    "finish_reason": choice.finish_reason or "stop",
                })

            # Обрабатываем tool_calls — здесь агент запрашивает вызов инструментов
            tool_results = []
            for tc in msg.tool_calls:
                tool_results.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "content": _safe_json({
                        "warning": f"Инструмент '{tc.function.name}' вызван, но MCP-хост должен выполнить его.",
                        "arguments": tc.function.arguments,
                    }),
                })
            history.extend(tool_results)

            # Если мы просто проходим по шагам без реального выполнения инструментов,
            # на следующей итерации агент получит предупреждения и может дать финальный ответ

        # Если достигнут лимит шагов
        return _safe_json({
            "agent_id": agent_id,
            "agent_name": agent_cfg["name"],
            "result": history[-1].get("content", "") if history else "",
            "steps": max_steps,
            "status": "max_steps_reached",
            "final_message": "Достигнут лимит шагов. Вот последний ответ агента.",
        })

    except Exception as e:
        return _safe_json({
            "agent_id": agent_id,
            "error": str(e),
            "type": type(e).__name__,
            "steps_completed": len(history),
        })


@mcp.tool()
def list_agents() -> str:
    """
    Список всех созданных агентов (из папки agents/).

    Returns:
        JSON со списком агентов: [{"agent_id": "...", "name": "...", "model": "..."}]
    """
    agents_dir = SERVER_DIR / "agents"
    if not agents_dir.exists():
        return _safe_json({"agents": [], "message": "Нет созданных агентов"})

    agents = []
    for f in sorted(agents_dir.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
            agents.append({
                "agent_id": cfg.get("agent_id", f.stem),
                "name": cfg.get("name", "?"),
                "model": cfg.get("model", "?"),
                "has_tools": len(cfg.get("tools", [])) > 0,
                "system_prompt_preview": (cfg.get("system_prompt", "") or "")[:120],
            })
        except Exception:
            agents.append({"agent_id": f.stem, "name": "?", "error": "Не удалось прочитать"})

    return _safe_json({"agents": agents, "count": len(agents)})


@mcp.tool()
def create_search_index(
    name: str,
    index_type: str = "text",
    description: str = "",
) -> str:
    """
    Создаёт поисковый индекс для хранения и поиска документов.

    Args:
        name: Имя индекса (уникальное)
        index_type: Тип: "text" (текстовый), "vector" (векторный), "hybrid" (гибридный)
        description: Описание индекса

    Returns:
        JSON с ID созданного индекса
    """
    sdk = get_sdk()

    try:
        si = sdk.search_indexes
        result = si.create(name=name, index_type=index_type, description=description)
        return _safe_json({
            "status": "created",
            "index_id": str(result.id) if hasattr(result, "id") else str(result),
            "name": name,
            "type": index_type,
        })
    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def search_in_index(
    index_id: str,
    query: str,
    top_k: int = 5,
) -> str:
    """
    Поиск по индексу (текстовому, векторному или гибридному).

    Args:
        index_id: ID индекса (из create_search_index)
        query: Поисковый запрос
        top_k: Число результатов

    Returns:
        JSON: {"results": [{"content": "...", "score": 0.95}, ...]}
    """
    sdk = get_sdk()

    try:
        si = sdk.search_indexes
        result = si.search(index_id=index_id, query=query, top_k=top_k)

        results = []
        if hasattr(result, "results"):
            for r in result.results:
                results.append({
                    "content": getattr(r, "content", str(r)),
                    "score": getattr(r, "score", None),
                })

        return _safe_json({"results": results, "query": query, "index_id": index_id})
    except Exception as e:
        return _safe_json({"error": str(e), "type": type(e).__name__})


# ============================================================
#  Resources
# ============================================================

@mcp.resource("config://server")
def server_config() -> str:
    """Текущая конфигурация сервера."""
    return _safe_json({
        "server": "Yandex AI Studio MCP Server",
        "version": "1.0.0",
        "default_model": _default_model,
        "folder_id": (os.getenv("YANDEX_FOLDER_ID", "") or "")[:12] + "***",
        "auth_method": "API_KEY" if os.getenv("YANDEX_API_KEY") else (
            "IAM_TOKEN" if os.getenv("YANDEX_IAM_TOKEN") else "NOT SET"
        ),
    })


# ============================================================
#  Entry Point
# ============================================================

if __name__ == "__main__":
    try:
        logger.info("Запуск Yandex AI Studio MCP Server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error("Критическая ошибка: %s", e)
        raise
