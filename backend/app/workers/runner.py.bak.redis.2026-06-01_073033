import socket
import threading
import time

from redis import Redis
from rq import Worker

from app.core.config import settings


def heartbeat(redis: Redis, worker_id: str) -> None:
    while True:
        redis.sadd("workers:heartbeat", worker_id)
        redis.expire("workers:heartbeat", 90)
        time.sleep(30)


def main() -> None:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    worker_id = f"{socket.gethostname()}:{time.time_ns()}"
    threading.Thread(target=heartbeat, args=(redis, worker_id), daemon=True).start()
    worker = Worker(["downloads:vip", "downloads"], connection=redis)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
