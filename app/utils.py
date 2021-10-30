import asyncio
import logging
from beanie.odm.operators.update.general import Set
from app.settings import CACHE_URL, TIME_TO_UPDATE_IN_MINUTES
import json
from app.registry_api import fetch_version, fetch_data_from_registry
from app.dbUtils.models import Package, UPDATE_STATUSES
from datetime import datetime, timedelta
import aioredis

redis = aioredis.from_url(CACHE_URL)
logger = logging.getLogger("package_manager")


async def validate_if_updated(package_name, simplified_version_name):
    """
    This method validates if the package name and specific version are updated in server.
    Return : Tuple (pk,pkg, is_updated) . pk_pkg of the format of `get_pk` and bool if updated in our server or not.
     """
    pk_pkg = get_pk(package_name=package_name, version=simplified_version_name)
    result_from_cache = await redis.get(pk_pkg)
    if result_from_cache is not None:
        return pk_pkg, True
    result_from_db = await Package.get(pk_pkg)
    if result_from_db is not None:
        if datetime.now() - result_from_db.last_updated_time <= timedelta(minutes=TIME_TO_UPDATE_IN_MINUTES):
            return pk_pkg, True

    return pk_pkg, False


def get_pk(package_name, version):
    """Return string contains the package name and version in order to save it in DB and Redis"""
    return f"{package_name}_{version}"


def get_fetched_pk(package_name, version):
    """Return string contains the fetched_pk for retrieving cache results of unsimplified versions."""
    return f"{get_pk(package_name=package_name, version=version)}_fetched"


async def update_package(package_name, version_name, session):
    """
    This method updates a package with simplified version by getting its data from the registry
    Later on, sends update task for each dependency it has.
    At the end, updates the Redis and DB with the package information.
    :param package_name: str representing the package name
    :param version_name: version name (simplified) and latest
    :param session: async session
    :return: id of pkg and version. in the format of `get_pk` method
    """
    logger.info(f"Starting to update {package_name} , {version_name}")
    data, status = await fetch_data_from_registry(package_name=package_name, version=version_name,
                                                  session=session)  # can return status code . Raise exception call to father.
    dependencies = data.get('dependencies', {})
    pk_current = get_pk(package_name=package_name, version=version_name)  # from simplified
    tasks = []
    for dependency_name, dependency_version in dependencies.items():
        logger.info(f"Starting async scan for {package_name}:{version_name}")
        try:
            version_simplified = await simplify_version(package_name=dependency_name,
                                                        package_version=dependency_version,
                                                        session=session)  # can return excpetion. Continue
            pk_pkg, updated = await validate_if_updated(package_name=package_name,
                                                        simplified_version_name=version_simplified)
            if not updated:
                task = asyncio.create_task(update_package(dependency_name, version_simplified, session))
                tasks.append(task)
        except Exception as e:
            logger.error(f"Exception in {dependency_name}, {dependency_version}. exception is: {e}")
            continue
    dependency_ids = await asyncio.gather(*tasks)
    package_to_insert = {'dependencies': dependency_ids, 'name': package_name, 'version': str(version_name)}
    logger.info(f"Insert {package_to_insert}")
    await redis.set(pk_current, json.dumps(package_to_insert))
    await Package.find_one(Package.id == pk_current).upsert(
        Set({Package.dependencies: package_to_insert['dependencies'],
             Package.name: package_to_insert['name'],
             Package.version: package_to_insert['version'],
             Package.last_updated_time: datetime.now(), Package.id: pk_current,
             Package.update_status: UPDATE_STATUSES['DONE']}),
        on_insert=Package(last_updated_time=datetime.now(), name=package_to_insert['name'],
                          version=package_to_insert['version'], dependencies=package_to_insert['dependencies'],
                          id=pk_current, update_status=UPDATE_STATUSES['DONE'])
    )
    return pk_current


async def simplify_version(package_name, package_version, session):  # can return exception
    """Simplify version to support semver format from unstructured format"""
    fetched_pk = get_fetched_pk(package_name, package_version)
    version_simplified = await redis.get(fetched_pk)
    if version_simplified is None:
        version_simplified = await fetch_version(package=package_name, version=package_version,
                                                 session=session)  # can return exception
        await redis.set(fetched_pk, str(version_simplified))
    else:
        if isinstance(version_simplified, bytes):
            version_simplified = version_simplified.decode('utf-8')
    return version_simplified


async def get_json_from_node(id: str) -> dict:
    """
    This method reads from Redis / Database and returns dict from node
    :param id: id of pkg and version. in the format of `get_pk` method
    :return: dict representing the node
    """
    cached = await redis.get(id)  # Json with dependencies as key and values and dependencies
    if cached is not None:
        return json.loads(cached)
    pk_object = await Package.get(id)
    return pk_object.dict()


async def get_json(node_pk):
    """
    This version gets the dict for the node, and creates a tree from it's dependencies by calling get_json on
    each dependency.
    """
    object = await get_json_from_node(node_pk)
    return {dependency_pk: await get_json(dependency_pk) for dependency_pk in object['dependencies']}


async def simplify_and_update(package_name: str, version_name: str, session) -> str:
    """
    This method simplifies the version and update it in the DB and Redis if necessary.
    :param package_name:str package_name
    :param version_name: version name unsimplified
    :param session:
    :return: id of pkg and version. in the format of `get_pk` method
    """
    logger.error("WTF?! simplify finaly")
    simplified_version = await simplify_version(package_name=package_name, package_version=version_name,
                                                session=session)  # can return exception
    pk_pkg, updated = await validate_if_updated(package_name=package_name,
                                                simplified_version_name=simplified_version)
    if not updated:
        pk_pkg = await update_package(package_name, simplified_version, session)  # Can return exception
    return pk_pkg
