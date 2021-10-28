from typing import Optional
import aiohttp
from fastapi import FastAPI

from pydantic import BaseModel

from utils import *


class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/{package_name}/{version}")
async def read_item(package_name: str, version: str, q: Optional[str] = None):
    print("read item")
    async with aiohttp.ClientSession() as session:
        print("session granted")
        result = await async_scan(package_name=package_name, version_name=version, session=session)
        return result


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}


@app.post("/items/")
def create_item(item: Item):
    return item
