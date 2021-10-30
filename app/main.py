import aiohttp
from fastapi import FastAPI
from app.dbUtils.db import *
from app.utils import simplify_and_update, get_json, redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from fastapi_cache.coder import JsonCoder
from app.settings import *

logger = logging.getLogger('package_manager')

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await connect_to_db()
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


@app.get("/{package_name}/{version}")
@cache(expire=60, coder=JsonCoder)
async def get_package(package_name: str, version: str):
    async with aiohttp.ClientSession() as session:
        print("session granted")
        pk_pkg = await simplify_and_update(package_name, version, session)
        result = await get_json(pk_pkg)
        return result
