from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "LIGHTHOUSE_"}

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "lighthouse"
    db_user: str = "lighthouse"
    db_password: str = ""

    # Auth
    google_client_id: str = ""
    google_client_secret: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # App
    environment: str = "development"
    allowed_origins: str = "https://lighthouse.jonathansilverstein.us"
    base_url: str = "https://lighthouse.jonathansilverstein.us"
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
