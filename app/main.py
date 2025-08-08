from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import time

from app.services.slack_service import process_slack_message, verify_slack_signature

# Crear la aplicación FastAPI
app = FastAPI(
    title="Wasi Slack AI",
    description="Asistente de ONG para Slack con AI y Google Calendar",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas básicas
@app.get("/")
async def root():
    return {"message": "Wasi Slack AI está funcionando! 🤖🏠"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "wasi-slack-ai"}

# Endpoint para webhooks de Slack
@app.post("/slack/events")
async def slack_events(request: Request):
    """Manejar eventos de Slack"""
    
    body = await request.body()
    signature = request.headers.get("X-Slack-Signature")
    timestamp = request.headers.get("X-Slack-Request-Timestamp")

    # Validación básica de headers requeridos
    if not signature or not timestamp:
        raise HTTPException(status_code=400, detail="Missing Slack signature headers")

    # Protección contra replay attacks (ventana de 5 minutos)
    try:
        request_ts = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Slack timestamp")
    if abs(time.time() - request_ts) > 60 * 5:
        raise HTTPException(status_code=400, detail="Stale Slack request")

    # Verificación de firma
    if not verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=403, detail="Invalid Slack signature")
    
    # Parsear JSON
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Challenge para verificación inicial de Slack
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}
    
    # Procesar evento
    if data.get("type") == "event_callback":
        response = await process_slack_message(data)
        return response
    
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)