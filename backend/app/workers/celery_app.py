from celery import Celery

from app.config import get_settings

settings = get_settings()
celery_app = Celery("healthcheck", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_always_eager=settings.celery_eager,
    task_eager_propagates=True,
    broker_connection_retry_on_startup=True,
    worker_concurrency=settings.celery_worker_concurrency,
)


def register_tasks() -> None:
    from app.workers import healthcheck_tasks  # noqa: F401


register_tasks()
