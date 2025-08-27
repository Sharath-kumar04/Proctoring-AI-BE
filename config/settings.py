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
    DB_TYPE: str = Field(default="sqlite", env="DB_TYPE")  # 'mysql' or 'sqlite'
    DB_USER: str = Field(default="root", env="MYSQLUSER")
    DB_PASSWORD: str = Field(default="mysecretpassword", env="MYSQL_ROOT_PASSWORD")
    DB_HOST: str = Field(default="localhost", env="MYSQLHOST")
    DB_NAME: str = Field(default="proctoring_ai", env="MYSQL_DATABASE")
    DB_PORT: int = Field(default=3306, env="MYSQLPORT")
    SQLITE_URL: str = Field(default="sqlite:///./test.db")

    # JWT settings
    JWT_SECRET_KEY: str = Field(default_factory=generate_secret_key)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Server settings
    SERVER_HOST: str = Field(default="0.0.0.0")
    SERVER_PORT: int = Field(default=8080, env="PORT")

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
