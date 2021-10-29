import os

STAGE = os.environ.get("STAGE", 'dev')
cache_url = "redis://localhost"
MONGO_HOST = 'localhost' if STAGE == 'dev' else "mongo"
MONGO_USER = os.environ.get("MONGO_DB_USER", "root")
MONGO_PASSWORD = os.environ.get("MONGO_DB_PASSWORD", "example")
MONGO_DB_PORT = int(os.environ.get('MONGO_DB_PORT', '27017'))
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "package_db")
SERVER_PORT = "8888"
MONGO_URI = rf"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_DB_PORT}/db1?authSource=admin"
TIME_TO_UPDATE_IN_HOURS = 30
