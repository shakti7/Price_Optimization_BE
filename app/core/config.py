from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SMTP_SERVER: str
    SMTP_PORT: int
    EMAIL_SENDER: str
    EMAIL_PASSWORD: str
    BACKEND_URL: str
    FRONTEND_URL: str
    JWT_SECRET_KEY: str

    class Config:
        env_file = ".env"  
        
settings = Settings()
