from app.dbUtils.db import connect_to_db
from app.dbUtils.models import Package
from datetime import timedelta, datetime
from app.utils import simplify_and_update
from app.settings import TIME_TO_UPDATE_IN_HOURS
import aiohttp
import asyncio


async def update():
    await connect_to_db()
    packages = await Package.find(
        Package.last_updated_time < datetime.now() - timedelta(hours=TIME_TO_UPDATE_IN_HOURS)).to_list()
    async with aiohttp.ClientSession() as session:
        print("session granted")
        tasks = []
        for package in packages:
            print(f"Starting to update package : {package.id} because last update time is: {package.last_updated_time}")
            task = asyncio.create_task(simplify_and_update(package.name, package.version, session))
            tasks.append(task)
        await asyncio.gather(*tasks)
