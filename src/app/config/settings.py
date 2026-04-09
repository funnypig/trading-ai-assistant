from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    finviz_api_key: str
    finviz_email: str
    finviz_password: str
    playwright_user_data_dir: str
    openai_api_key: str
    anthropic_api_key: str
    redis_url: str = "redis://localhost:6379/0"
    supabase_db_url: str

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
