import asyncio
import aioredis
from beanie.odm.operators.update.general import Set

from app.settings import cache_url, TIME_TO_UPDATE_IN_HOURS
import json
from app.registry_api import *
import time
import aiohttp
from app.dbUtils.models import Package
from datetime import datetime, timedelta
from fastapi import BackgroundTasks

redis = aioredis.from_url(cache_url)
url = "https://registry.npmjs.org"


async def validate_if_updated(package_name, simplified_version_name):
    pk_pkg = get_pk(package_name=package_name, version=simplified_version_name)
    result_from_cache = await redis.get(pk_pkg)
    print(f"Result from cache is : {result_from_cache}")
    if result_from_cache is not None:
        return pk_pkg, True
    result_from_db = await Package.get(pk_pkg)
    print(f"Result from db is : {result_from_db}")
    if result_from_db is not None:
        if datetime.now() - result_from_db.last_updated_time <= timedelta(hours=TIME_TO_UPDATE_IN_HOURS):
            return pk_pkg, True

    return pk_pkg, False


def get_pk(package_name, version):
    return f"{package_name}_{version}"


def get_fetched_pk(package_name, version):
    return f"{get_pk(package_name=package_name, version=version)}_fetched"


async def update_package(package_name, version_name, session):
    """
    INV:: Fetch have been happened.
    :param package_name:
    :param version_name: version name (simplified) and latest
    :param session:
    :return:
    """
    start_time = time.time()
    data = await fetch_data_from_registry(package_name=package_name, version=version_name, session=session)
    dependencies = data.get('dependencies', {})
    pk_current = get_pk(package_name=package_name, version=version_name)  # from simplified
    tasks = []
    for dependency_name, dependency_version in dependencies.items():
        print(f"Starting async scan for {package_name}:{version_name}")
        version_simplified = await get_simplified_from_unsimplified(package_name=dependency_name,
                                                                    package_version=dependency_version,
                                                                    session=session)
        pk_pkg, updated = await validate_if_updated(package_name=package_name,
                                                    simplified_version_name=version_simplified)
        if not updated:
            task = asyncio.create_task(update_package(dependency_name, version_simplified, session))
            tasks.append(task)
    dependency_ids = await asyncio.gather(*tasks)
    package_to_insert = {'dependencies': dependency_ids, 'name': package_name, 'version': str(version_name)}
    await redis.set(pk_current, json.dumps(package_to_insert))
    await Package.find_one(Package.id == pk_current).upsert(
        Set({Package.dependencies: package_to_insert['dependencies'],
             Package.name: package_to_insert['name'],
             Package.version: package_to_insert['version'],
             Package.last_updated_time: datetime.now(), Package.id: pk_current}),
        on_insert=Package(last_updated_time=datetime.now(), name=package_to_insert['name'],
                          version=package_to_insert['version'], dependencies=package_to_insert['dependencies'],
                          id=pk_current)
    )
    print(f"UPDATE PACKAGE: {package_name} took {time.time() - start_time}")
    return pk_current


async def get_simplified_from_unsimplified(package_name, package_version, session):
    start_time = time.time()
    fetched_pk = get_fetched_pk(package_name, package_version)
    version_simplified = await redis.get(fetched_pk)
    if version_simplified is None:
        version_simplified = await fetch_version(package=package_name, version=package_version,
                                                 session=session)
        await redis.set(fetched_pk, str(version_simplified))
    else:
        print(f"SIMPLIFY VERSION for {package_name} - {package_version} got from redis")
    print(f"SIMPLIFY VERSION for {package_name} - {package_version} took: {time.time() - start_time}")
    if isinstance(version_simplified, bytes):
        version_simplified = version_simplified.decode('utf-8')
    return version_simplified


async def get_json_from_node(id: str):
    """"""
    cached = await redis.get(id)  # Json with dependencies as k and values and dependencies
    if cached is not None:
        return json.loads(cached)
    pk_object = await Package.get(id)
    return pk_object.dict()


async def get_json(node_pk):
    object = await get_json_from_node(node_pk)
    return {dependency_pk: await get_json(dependency_pk) for dependency_pk in object['dependencies']}


async def simplify_and_update(package_name, version_name, session):
    simplified_version = await get_simplified_from_unsimplified(package_name=package_name, package_version=version_name,
                                                                session=session)
    pk_pkg, updated = await validate_if_updated(package_name=package_name,
                                                simplified_version_name=simplified_version)
    if not updated:
        pk_pkg = await update_package(package_name, simplified_version, session)
    return pk_pkg
