from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Configuración de la aplicación
    app_name: str = "Wasi Assistant"
    debug: bool = False
    
    # APIs externas
    slack_bot_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_credentials_path: Optional[str] = None
    
    # Base de datos (para más adelante)
    database_url: Optional[str] = None
    
    class Config:
        env_file = ".env"

# Instancia global de configuración
settings = Settings()