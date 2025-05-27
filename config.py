from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Only define the one “broker” env var in HOST:PORT format
    REDIS_BROKER: str = Field(
        "localhost:6379",
        description="Redis broker in host:port format, e.g. localhost:6379",
    )

    WORKER_QUEUE: str = Field(
        "fastapi-app-queue-1",
        description="Redis queue to listen to for jobs",
    )

    # These two will be filled in by our validator
    redis_host: str
    redis_port: int

    # This runs before any other parsing, so we can split out host & port
    @model_validator(mode="before")
    @classmethod
    def _split_redis_broker(cls, values):
        broker = values.get("REDIS_BROKER", "localhost:6379")
        host, port_str = broker.split(":", 1)
        # overwrite/add our computed fields
        values["redis_host"] = host
        values["redis_port"] = int(port_str)
        return values

    # pydantic v2 way to point to an .env file
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
