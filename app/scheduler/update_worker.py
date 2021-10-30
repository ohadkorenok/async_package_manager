from app.scheduler.update_packages import update
from app.settings import  WORKER_TIME_TO_SLEEP_IN_SECONDS
import asyncio


async def forever():
    while True:
        await update()
        await asyncio.sleep(WORKER_TIME_TO_SLEEP_IN_SECONDS)


loop = asyncio.get_event_loop()
loop.run_until_complete(forever())

