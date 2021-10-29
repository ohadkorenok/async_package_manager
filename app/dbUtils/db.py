from pymongo import MongoClient
from app.settings import *
import motor.motor_asyncio
from beanie import init_beanie
from app.dbUtils.models import Package, __beanie_models__
mongo_client = MongoClient(MONGO_URI)


async def connect_to_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    await init_beanie(
        database=client[MONGO_DB_NAME], document_models=__beanie_models__
    )
