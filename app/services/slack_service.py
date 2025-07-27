import json
import hmac
import hashlib
import requests
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

async def send_slack_message(channel: str, text: str, thread_ts: str = None):
    """Enviar mensaje usando Slack Web API"""
    if not settings.slack_bot_token:
        return False
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {settings.slack_bot_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "channel": channel,
        "text": text
    }
    
    # Si hay thread, responder en el thread
    if thread_ts:
        payload["thread_ts"] = thread_ts
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        return result.get('ok', False)
    except Exception:
        return False

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
    
    # Generar respuesta según el comando
    response_text = ""
    
    if 'hello' in text or 'hola' in text:
        response_text = f"¡Hola <@{user}>! Soy Wasi Assistant 🏠\n¿En qué puedo ayudarte hoy?"
        
    elif 'help' in text or 'ayuda' in text:
        response_text = (
            f"🤖 *Wasi Assistant - Comandos disponibles:*\n\n"
            f"• `hello` - Saludo\n"
            f"• `help` - Mostrar esta ayuda\n"
            f"• `status` - Estado del sistema\n\n"
            f"_Próximamente: crear reuniones, buscar contactos y más!_"
        )
        
    elif 'status' in text or 'estado' in text:
        response_text = (
            f"✅ *Estado del sistema:*\n"
            f"• Slack: Conectado\n"
            f"• Servidor: Funcionando\n"
            f"• Usuario: <@{user}>\n"
            f"• Canal: <#{channel}>"
        )
        
    else:
        # Respuesta por defecto
        response_text = (
            f"Recibí tu mensaje: _{text}_\n\n"
            f"Escribe `help` para ver qué puedo hacer 🤖"
        )
    
    # Enviar respuesta
    await send_slack_message(channel, response_text, thread_ts)
    
    return {"status": "processed"}