The Worker service is implemented in `backend/app/workers` so it can share the same SQLAlchemy models, settings, and service code as the FastAPI API.

Docker Compose starts it with:

```sh
python -m app.workers.runner
```

The scheduler runs separately with:

```sh
python -m app.workers.scheduler
```
