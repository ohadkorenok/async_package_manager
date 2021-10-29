from app.scheduler.update_packages import update
import asyncio
from time import sleep


async def forever():
    while True:
        await update()
        await asyncio.sleep(40)


loop = asyncio.get_event_loop()
loop.run_until_complete(forever())
