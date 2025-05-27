from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_HOST: str = Field(..., description="REDIS_HOST")
    REDIS_PORT: int = Field(..., description="REDIS_PORT")

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
