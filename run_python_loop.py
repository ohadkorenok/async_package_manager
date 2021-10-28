import asyncio
import aiohttp
from utils import *

package_name = 'express'
version = 'latest'


async def main():
    async with aiohttp.ClientSession() as session:
        result = await async_scan(package_name=package_name, version_name=version, session=session)
        print (result)

asyncio.run(main())