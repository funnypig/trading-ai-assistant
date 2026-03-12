from pydantic_settings import BaseSettings


SMART_MODEL = "openai:gpt-5.4"
DATA_ANALYSIS_MODEL = "claude-sonnet-4-6"
MINI_MODEL = "openai:gpt-5-mini"


class Settings(BaseSettings):
    finviz_api_key: str
    finviz_email: str
    finviz_password: str
    playwright_user_data_dir: str
    openai_api_key: str
    anthropic_api_key: str
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
