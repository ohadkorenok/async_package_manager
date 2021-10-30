from pymongo import MongoClient
from app.settings import *
import motor.motor_asyncio
from beanie import init_beanie
from app.dbUtils.models import __beanie_models__

mongo_client = MongoClient(MONGO_URI)


async def connect_to_db(db_name=None):
    if db_name is None:
        db_name = MONGO_DB_NAME
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    await init_beanie(
        database=client[db_name], document_models=__beanie_models__
    )
