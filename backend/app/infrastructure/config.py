import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Base de datos (variables sueltas — fallback cuando no hay DATABASE_URL) ---
    mariadb_user: str = "asistente"
    mariadb_password: str = "asistente_pass"
    mariadb_db: str = "asistente_db"
    mariadb_host: str = "db"
    mariadb_port: int = 3306

    # --- LLM provider: "ollama" | "groq" | "anthropic" ---
    llm_provider: str = "ollama"
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b-instruct-q4_K_M"
    ollama_embed_model: str = "nomic-embed-text"

    groq_api_key: str = ""
    groq_model: str = "qwen-2.5-7b-instruct"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    redis_url: str = "redis://redis:6379/0"

    app_locale: str = "es_BO"
    app_currency: str = "BOB"

    @property
    def database_url(self) -> str:
        # DATABASE_URL tiene prioridad (cloud). Fallback: variables sueltas (local).
        url = os.getenv("DATABASE_URL")
        if url:
            return url.replace("mysql+aiomysql://", "mysql+pymysql://")
        return (
            f"mysql+pymysql://{self.mariadb_user}:{self.mariadb_password}"
            f"@{self.mariadb_host}:{self.mariadb_port}/{self.mariadb_db}?charset=utf8mb4"
        )


settings = Settings()
