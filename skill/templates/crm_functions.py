"""
CRM Integration Functions for Yandex AI Studio MCP Server
=========================================================
Готовые функции для добавления в server.py.
Подключаются как @mcp.tool() инструменты.

Требует переменные в .env:
  AMOCRM_SUBDOMAIN, AMOCRM_ACCESS_TOKEN
  BITRIX24_WEBHOOK  (полный URL вида https://domain.bitrix24.ru/rest/1/token/)
  RETAILCRM_DOMAIN, RETAILCRM_API_KEY
"""

import os
import json
import requests


# ============================================================
#  amoCRM (REST API v4)
# ============================================================

def _amocrm_request(method: str, path: str, data: dict | None = None) -> dict:
    """Базовый запрос к amoCRM API v4."""
    subdomain = os.getenv("AMOCRM_SUBDOMAIN", "")
    token = os.getenv("AMOCRM_ACCESS_TOKEN", "")
    url = f"https://{subdomain}.amocrm.ru{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if method == "GET":
        resp = requests.get(url, headers=headers, params=data)
    elif method == "POST":
        resp = requests.post(url, headers=headers, json=data)
    elif method == "PATCH":
        resp = requests.patch(url, headers=headers, json=data)
    else:
        raise ValueError(f"Unsupported method: {method}")
    return resp.json()


def create_amocrm_lead(
    name: str,
    price: float = 0,
    pipeline_id: int = 0,
    status_id: int = 0,
    contact_name: str = "",
    contact_phone: str = "",
    contact_email: str = "",
    tags: str = "",
) -> str:
    """
    Создать сделку в amoCRM с контактом.

    Args:
        name: Название сделки
        price: Бюджет
        pipeline_id: ID воронки (0 = основная)
        status_id: ID этапа (0 = первый)
        contact_name: Имя контакта
        contact_phone: Телефон
        contact_email: Email
        tags: Теги через запятую

    Returns:
        JSON с id созданной сделки и контакта
    """
    lead_data = {
        "name": name,
        "price": int(price),
        "pipeline_id": pipeline_id,
        "status_id": status_id,
    }
    if tags:
        lead_data["tags_to_add"] = [{"name": t.strip()} for t in tags.split(",")]

    body = [lead_data]

    # Встраиваем контакт
    if contact_name or contact_phone or contact_email:
        contact = {"first_name": contact_name or "Клиент"}
        custom_fields = []
        if contact_phone:
            custom_fields.append({"field_code": "PHONE", "values": [{"value": contact_phone}]})
        if contact_email:
            custom_fields.append({"field_code": "EMAIL", "values": [{"value": contact_email}]})
        if custom_fields:
            contact["custom_fields_values"] = custom_fields
        body[0]["_embedded"] = {"contacts": [contact]}

    result = _amocrm_request("POST", "/api/v4/leads", body)
    return json.dumps(result, ensure_ascii=False, indent=2)


def find_amocrm_contact(query: str) -> str:
    """
    Найти контакт в amoCRM по телефону или email.

    Args:
        query: Телефон или email для поиска

    Returns:
        JSON с найденными контактами
    """
    result = _amocrm_request("GET", "/api/v4/contacts", {"query": query})
    return json.dumps(result, ensure_ascii=False, indent=2)


def create_amocrm_task(
    lead_id: int,
    text: str,
    responsible_user_id: int = 0,
    complete_till: str = "",
) -> str:
    """
    Создать задачу в amoCRM, привязанную к сделке.

    Args:
        lead_id: ID сделки
        text: Текст задачи
        responsible_user_id: ID ответственного (0 = текущий пользователь)
        complete_till: Дедлайн (unixtime)

    Returns:
        JSON с id задачи
    """
    import time
    if not complete_till:
        complete_till = str(int(time.time()) + 86400)  # +24 часа

    body = [{
        "text": text,
        "complete_till": int(complete_till),
        "entity_id": lead_id,
        "entity_type": "leads",
        "responsible_user_id": responsible_user_id,
    }]
    result = _amocrm_request("POST", "/api/v4/tasks", body)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
#  Bitrix24 (REST API)
# ============================================================

def _bitrix_request(method: str, params: dict | None = None) -> dict:
    """Базовый запрос к Bitrix24 REST API."""
    webhook = os.getenv("BITRIX24_WEBHOOK", "")
    if not webhook:
        raise RuntimeError("BITRIX24_WEBHOOK не задан в .env")
    url = f"{webhook.rstrip('/')}/{method}"
    resp = requests.post(url, json=params or {})
    return resp.json()


def create_bitrix_lead(
    title: str,
    name: str = "",
    phone: str = "",
    email: str = "",
    source_description: str = "",
    comments: str = "",
) -> str:
    """
    Создать лид в Bitrix24 CRM.

    Args:
        title: Название лида
        name: Имя контакта
        phone: Телефон
        email: Email
        source_description: Источник заявки
        comments: Комментарий

    Returns:
        JSON с ID созданного лида
    """
    fields = {"TITLE": title}
    if name:
        fields["NAME"] = name
    if phone:
        fields["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "WORK"}]
    if email:
        fields["EMAIL"] = [{"VALUE": email, "VALUE_TYPE": "WORK"}]
    if source_description:
        fields["SOURCE_DESCRIPTION"] = source_description
    if comments:
        fields["COMMENTS"] = comments

    result = _bitrix_request("crm.lead.add", {"fields": fields})
    return json.dumps(result, ensure_ascii=False, indent=2)


def create_bitrix_deal(
    title: str,
    opportunity: float = 0,
    contact_name: str = "",
    contact_phone: str = "",
    comments: str = "",
) -> str:
    """
    Создать сделку в Bitrix24 CRM.

    Args:
        title: Название сделки
        opportunity: Сумма сделки
        contact_name: Имя контакта
        contact_phone: Телефон
        comments: Комментарий

    Returns:
        JSON с ID сделки
    """
    fields = {
        "TITLE": title,
        "OPPORTUNITY": opportunity,
        "COMMENTS": comments,
    }
    if contact_name or contact_phone:
        # Сначала создаём контакт
        contact_fields = {}
        if contact_name:
            contact_fields["NAME"] = contact_name
        if contact_phone:
            contact_fields["PHONE"] = [{"VALUE": contact_phone, "VALUE_TYPE": "WORK"}]
        contact_result = _bitrix_request("crm.contact.add", {"fields": contact_fields})
        if "result" in contact_result and contact_result["result"]:
            fields["CONTACT_ID"] = contact_result["result"]

    result = _bitrix_request("crm.deal.add", {"fields": fields})
    return json.dumps(result, ensure_ascii=False, indent=2)


def search_bitrix_contacts(query: str) -> str:
    """
    Поиск контактов в Bitrix24.

    Args:
        query: Строка поиска (имя, телефон, email)

    Returns:
        JSON с найденными контактами
    """
    result = _bitrix_request("crm.contact.list", {
        "filter": {"SEARCH_CONTENT": query},
        "select": ["ID", "NAME", "LAST_NAME", "PHONE", "EMAIL"],
    })
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
#  RetailCRM (REST API v5)
# ============================================================

def _retailcrm_request(method: str, path: str, data: dict | None = None) -> dict:
    """Базовый запрос к RetailCRM API v5."""
    domain = os.getenv("RETAILCRM_DOMAIN", "")
    api_key = os.getenv("RETAILCRM_API_KEY", "")
    url = f"https://{domain}.retailcrm.ru{path}"
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    if method == "GET":
        resp = requests.get(url, headers=headers, params=data)
    else:
        resp = requests.post(url, headers=headers, json=data)
    return resp.json()


def create_retailcrm_order(
    customer_name: str = "",
    customer_phone: str = "",
    customer_email: str = "",
    items: str = "[]",
    total: float = 0,
    source: str = "ai-agent",
) -> str:
    """
    Создать заказ в RetailCRM.

    Args:
        customer_name: Имя клиента
        customer_phone: Телефон (обязательно)
        customer_email: Email
        items: JSON-строка с товарами [{"productName": "...", "quantity": 1, "initialPrice": 100}]
        total: Итоговая сумма
        source: Источник заказа

    Returns:
        JSON с ID заказа
    """
    import json as _json

    order = {
        "customer": {"phones": [{"number": customer_phone}]},
        "source": {"source": source},
    }
    if customer_name:
        order["firstName"] = customer_name
    if customer_email:
        order["customer"]["email"] = customer_email
    if items:
        order["items"] = _json.loads(items) if isinstance(items, str) else items
    if total:
        order["totalSumm"] = total

    result = _retailcrm_request("POST", "/api/v5/orders/create", {"order": _json.dumps(order)})
    return _json.dumps(result, ensure_ascii=False, indent=2)


def search_retailcrm_orders(customer_phone: str) -> str:
    """
    Найти заказы клиента по телефону.

    Args:
        customer_phone: Телефон клиента

    Returns:
        JSON со списком заказов
    """
    result = _retailcrm_request("GET", "/api/v5/orders", {
        "filter": {"customerPhone": customer_phone},
        "limit": 10,
    })
    return json.dumps(result, ensure_ascii=False, indent=2)
