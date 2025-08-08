import json
import hmac
import hashlib
from typing import Awaitable, Callable, Optional

from slack_sdk.web.async_client import AsyncWebClient
from app.config import settings

def verify_slack_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    """Verificar que el request viene de Slack"""
    if not settings.slack_signing_secret:
        return True  # Skip en desarrollo
    
    sig_basestring = f'v0:{timestamp}:{request_body.decode()}'
    expected_signature = 'v0=' + hmac.new(
        settings.slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

async def send_slack_message(channel: str, text: str, thread_ts: Optional[str] = None) -> bool:
    """Enviar mensaje usando Slack Web API (async, no bloqueante)."""
    if not settings.slack_bot_token:
        return False

    client = AsyncWebClient(token=settings.slack_bot_token)
    try:
        kwargs = {"channel": channel, "text": text}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        resp = await client.chat_postMessage(**kwargs)
        return bool(resp.get("ok", False))
    except Exception:
        return False

# ------------------
# Command routing
# ------------------
CommandHandler = Callable[[str, str], Awaitable[str]]

async def handle_hello(user: str, channel: str) -> str:
    return f"¡Hola <@{user}>! Soy Wasi Assistant 🏠\n¿En qué puedo ayudarte hoy?"

async def handle_help(user: str, channel: str) -> str:
    return (
        "🤖 *Wasi Assistant - Comandos disponibles:*\n\n"
        "• `hello` - Saludo\n"
        "• `help` - Mostrar esta ayuda\n"
        "• `status` - Estado del sistema\n\n"
        "_Próximamente: crear reuniones, buscar contactos y más!_"
    )

async def handle_status(user: str, channel: str) -> str:
    return (
        "✅ *Estado del sistema:*\n"
        "• Slack: Conectado\n"
        f"• Usuario: <@{user}>\n"
        f"• Canal: <#{channel}>"
    )

async def handle_default(user: str, channel: str, text: str) -> str:
    return (
        f"Recibí tu mensaje: _{text}_\n\n"
        "Escribe `help` para ver qué puedo hacer 🤖"
    )

async def process_slack_message(event_data: dict) -> dict:
    """Procesar mensaje de Slack"""
    
    event = event_data.get('event', {})
    
    # Evitar loops infinitos - ignorar mensajes del propio bot
    if event.get('bot_id') or event.get('subtype') == 'bot_message':
        return {"status": "ignored_bot_message"}
    
    text = event.get('text', '').lower()
    user = event.get('user', '')
    channel = event.get('channel', '')
    thread_ts = event.get('thread_ts')
    
    # Enrutamiento simple de comandos
    handlers: list[tuple[list[str], CommandHandler]] = [
        (["hello", "hola"], handle_hello),
        (["help", "ayuda"], handle_help),
        (["status", "estado"], handle_status),
    ]

    response_text: str
    matched = False
    for keywords, handler in handlers:
        if any(k in text for k in keywords):
            response_text = await handler(user, channel)
            matched = True
            break

    if not matched:
        response_text = await handle_default(user, channel, text)
    
    # Enviar respuesta
    await send_slack_message(channel, response_text, thread_ts)
    
    return {"status": "processed"}