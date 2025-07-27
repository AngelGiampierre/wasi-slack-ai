from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Crear la aplicación FastAPI
app = FastAPI(
    title="Wasi Assistant Slack AI",
    description="Asistente de ONG para Slack con integración a Google Calendar",
    version="1.0.0",
)

# Configurar CORS (para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas básicas
@app.get("/")
async def root():
    return {"message": "Wasi Assistant está funcionando! 🏠"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "wasi-assistant"}

# Endpoint para webhooks de Slack (placeholder)
@app.post("/slack/events")
async def slack_webhook():
    return {"status": "received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)