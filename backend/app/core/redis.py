from collections.abc import Generator

from redis import Redis

from app.core.config import settings


def get_redis() -> Generator[Redis, None, None]:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        client.close()
