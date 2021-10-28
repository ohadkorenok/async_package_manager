import os
import asyncio
from utils import updater_runner
from celery import Celery

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
app = Celery('tasks_handler.update_package_from_main_package', broker=BROKER_URL,
             backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379"))


@app.task(name="update_package_from_main_package")
def update_package_from_main_package(package_name, simplified_version):
    print("CELERY!!!! IN HANDLE ENTRY")
    # task = asyncio.create_task(update_package(package_name, simplified_version))
    result = asyncio.run(updater_runner(package_name, simplified_version))
    print(f"result is: {result}")
    return result
