from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""
    SESSION_SECRET: str
    LEARNER_PASSWORD_HASH: str
    SESSION_COOKIE_MAX_AGE_DAYS: int = 30
    SESSION_COOKIE_SECURE: bool = True
    LEARNER_TIMEZONE: str = "Asia/Ho_Chi_Minh"

    AI_PROVIDER: str = "claude"
    ANTHROPIC_API_KEY: str = ""


settings = Settings()
