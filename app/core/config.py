from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "B.A.R.N.A.B.Y Core AI"
    DEBUG: bool = False
    
    # AI Engine Endpoints
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    TEXT_MODEL: str = "qwen2.5:7b"
    VISION_MODEL: str = "qwen2-vl:latest"  # or llava:latest
    WHISPER_MODEL_SIZE: str = "small.en"  # Optimized for speed on 5060 Ti
    
    # Camera Configs
    TAPO_OUTSIDE_RTSP: str = Field(default="", env="TAPO_OUTSIDE_RTSP")
    TAPO_KITCHEN_RTSP: str = Field(default="", env="TAPO_KITCHEN_RTSP")
    
    # Scribe Memory Lifespan (seconds)
    SCRIBE_SESSION_TIMEOUT: int = 14400  # Auto-purge RAM after 4 hours idle
    
    class Config:
        env_file = ".env"

settings = Settings()