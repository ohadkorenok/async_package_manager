import os
import logging

logger = logging.getLogger('package_manager')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('package_manager.log')
fh.setLevel(logging.INFO)
logger.addHandler(fh)

worker_logger = logging.getLogger('worker_logger')
worker_logger.setLevel(logging.INFO)
fh = logging.FileHandler('worker_logger.log')
fh.setLevel(logging.INFO)
worker_logger.addHandler(fh)

STAGE = os.environ.get("STAGE", 'dev')
REDIS_HOST = 'localhost' if STAGE == 'dev' else "redis:6379"
CACHE_URL = f"redis://{REDIS_HOST}"
MONGO_HOST = 'localhost' if STAGE == 'dev' else "mongo"
MONGO_USER = os.environ.get("MONGO_DB_USER", "root")
MONGO_PASSWORD = os.environ.get("MONGO_DB_PASSWORD", "example")
MONGO_DB_PORT = int(os.environ.get('MONGO_DB_PORT', '27017'))
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "package_db")
SERVER_PORT = "8888"
MONGO_URI = rf"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_DB_PORT}/db1?authSource=admin"
TIME_TO_UPDATE_IN_MINUTES = int(os.environ.get("TIME_TO_UPDATE_IN_MINUTES", '30'))
WORKER_TIME_TO_SLEEP_IN_SECONDS = int(os.environ.get("WORKER_TIME_TO_SLEEP_IN_SECONDS", '60'))
NUMBER_OF_DOCUMENTS_TO_UPDATE = int(os.environ.get("NUMBER_OF_DOCUMENTS_TO_UPDATE", '10'))
REGISTRY_URL = "https://registry.npmjs.org"
