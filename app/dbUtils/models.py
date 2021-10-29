from beanie import Document, Indexed, init_beanie
from typing import List
from datetime import datetime


class Package(Document):
    name: str
    version: str
    id: Indexed(str)
    dependencies: List[str]
    last_updated_time: datetime


__beanie_models__ = [Package]
