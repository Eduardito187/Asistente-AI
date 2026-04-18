from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mariadb_user: str = "asistente"
    mariadb_password: str = "asistente_pass"
    mariadb_db: str = "asistente_db"
    mariadb_host: str = "db"
    mariadb_port: int = 3306

    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b-instruct-q4_K_M"

    app_locale: str = "es_BO"
    app_currency: str = "BOB"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mariadb_user}:{self.mariadb_password}"
            f"@{self.mariadb_host}:{self.mariadb_port}/{self.mariadb_db}?charset=utf8mb4"
        )


settings = Settings()
