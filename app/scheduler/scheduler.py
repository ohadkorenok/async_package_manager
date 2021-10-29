from app.dbUtils.models import Package
import asyncio
from pytz import utc
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from app.scheduler.update_packages import update
from app.settings import TIME_TO_UPDATE_IN_HOURS
from datetime import datetime, timedelta
from app.dbUtils.db import mongo_client
import pytz
import logging


def main():
    logging.basicConfig()
    logger = logging.getLogger('apscheduler')
    jobstores = {
        'default': MemoryJobStore(),
        # 'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }
    executors = {
        'default': AsyncIOExecutor(),
        'processpool': ProcessPoolExecutor(5)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 1
    }
    scheduler = AsyncIOScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc,
                                 logger=logger)
    scheduler.add_job(update, trigger='interval', seconds=10,
                      start_date=datetime.now(),
                      end_date=datetime.now() + + timedelta(seconds=40),
                      timezone=pytz.utc,
                      args=[])
    scheduler.start()


if __name__ == '__main__':
    main()
