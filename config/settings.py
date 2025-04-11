from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

def generate_secret_key():
    return os.getenv("JWT_SECRET_KEY") or secrets.token_hex(64)

class Settings(BaseSettings):
    # Database settings
    DB_USER: str = Field(default=os.getenv("MYSQLUSER", "root"))
    DB_PASSWORD: str = Field(default=os.getenv("MYSQL_ROOT_PASSWORD", "1234567890"))
    DB_HOST: str = Field(default=os.getenv("MYSQLHOST", "localhost"))
    DB_NAME: str = Field(default=os.getenv("MYSQL_DATABASE", "defaultdb"))
    DB_PORT: int = Field(default=int(os.getenv("MYSQLPORT", "3306")))
    
    # MySQL settings
    MYSQL_URL: str = Field(default=os.getenv("MYSQL_URL", ""))
    MYSQL_DATABASE: str = Field(default=os.getenv("MYSQL_DATABASE", ""))
    MYSQLUSER: str = Field(default=os.getenv("MYSQLUSER", ""))
    MYSQLHOST: str = Field(default=os.getenv("MYSQLHOST", ""))
    MYSQLPASSWORD: str = Field(default=os.getenv("MYSQLPASSWORD", "1234567890"))
    MYSQLPORT: str = Field(default=os.getenv("MYSQLPORT", ""))
    MYSQLDATABASE: str = Field(default=os.getenv("MYSQLDATABASE", ""))

    # JWT settings
    JWT_SECRET_KEY: str = Field(default_factory=generate_secret_key)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Server settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = Field(default=int(os.getenv("PORT", "8081")))
    PORT: str = Field(default=os.getenv("PORT", "8081"))

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment variables

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
