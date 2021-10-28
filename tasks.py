import os
import time

from celery import Celery
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
app = Celery('package_handler', broker=BROKER_URL)

# celery = Celery(__name__)


@app.task(name="update_package_from_main_package")
def update_package_from_main_package(task_type):
    time.sleep(int(task_type) * 10)
    return True