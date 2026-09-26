from app.services.healthcheck_service import execute_run
from app.workers.celery_app import celery_app


@celery_app.task(name="healthcheck.execute")
def run_healthcheck(run_id: str) -> str:
    execute_run(run_id)
    return run_id
