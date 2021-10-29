import aiohttp
from fastapi import FastAPI
from app.scan import async_scan
from typing import Optional, List
from pydantic import BaseModel, BaseSettings
import motor.motor_asyncio
from app.dbUtils.models import __beanie_models__, Package, init_beanie
from app.dbUtils.db import *
from datetime import datetime


class Settings(BaseSettings):
    mongo_connection: str
    mongo_db = "package_db"


class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await connect_to_db()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/{package_name}/{version}")
async def get_package(package_name: str, version: str):
    async with aiohttp.ClientSession() as session:
        print("session granted")
        result = await async_scan(package_name=package_name, version_name=version, session=session)
        return result


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}


@app.post("/packages/")
async def create_item(package: Package):
    tony_bar = Package(name='Ohad', version='~1.5.2', last_updated_time=datetime.now(), dependencies=['Joshua_2.15.2'],
                       id="ohad_1.5.7")
    await tony_bar.insert()
    return package
