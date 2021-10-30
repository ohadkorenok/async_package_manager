from beanie import Document, Indexed, init_beanie
from typing import List
from datetime import datetime

UPDATE_STATUSES = {
    "IN_PROGRESS": 1,
    "DONE": 2
}


class Package(Document):
    name: str
    version: str
    id: Indexed(str)
    dependencies: List[str]
    last_updated_time: datetime
    update_status: int


__beanie_models__ = [Package]
