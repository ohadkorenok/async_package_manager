import asyncio
import aiohttp
from scan import *

# package_name = 'express'
package_name = 'async'
# version = 'latest'
version = '2.0.1'


async def main():
    async with aiohttp.ClientSession() as session:
        result = await async_scan(package_name=package_name, version_name=version, session=session)
        print (result)

asyncio.run(main())