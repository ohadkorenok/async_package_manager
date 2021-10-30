from app.dbUtils.db import connect_to_db
from app.dbUtils.models import Package, UPDATE_STATUSES
from datetime import timedelta, datetime
from app.utils import simplify_and_update
from app.settings import *
import aiohttp
import asyncio
import logging

logger = logging.getLogger("worker_logger")


async def update(size: int = NUMBER_OF_DOCUMENTS_TO_UPDATE):
    """
    Update function.
    Query the packages that are not in progress and last update time is greater than `TIME_TO_UPDATE_IN_MINUTES` variable
    Update the packages to have `in_progress` `update_status` value
    Update the packages using update_package.
    :param size: int for how many packages to update.
    :return: None
    """
    await connect_to_db()
    logger.info("Starting packages update")
    packages = Package.find(
        Package.last_updated_time < datetime.now() - timedelta(minutes=TIME_TO_UPDATE_IN_MINUTES),
        Package.update_status != UPDATE_STATUSES['IN_PROGRESS'], limit=size)
    package_list = await packages.to_list()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for package in package_list:
            await package.set({Package.update_status: UPDATE_STATUSES['IN_PROGRESS']})
            logger.info(
                f"Starting to update package : {package.id} because last update time is: {package.last_updated_time}."
                f"package status is: {package.update_status}")
            task = asyncio.create_task(simplify_and_update(package.name, package.version, session))
            tasks.append(task)
        await asyncio.gather(*tasks)
