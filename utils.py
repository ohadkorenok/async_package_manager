import requests
import semantic_version
import asyncio
import aioredis
from settings import cache_url
import json
from fastapi import BackgroundTasks, FastAPI

import time

redis = aioredis.from_url(cache_url)
# await redis.set("my-key", "value")
# value = await redis.get("my-key")

url = "https://registry.npmjs.org"


async def fetch_versions(package_name, session):
    async with session.get(f"{url}/{package_name}") as response:
        response = await response.json()
        return [semantic_version.Version(i) for i in response['versions'].keys()]


def get_versions(package_name):
    """
    This method gets all of the versions of a specific package name
    :param package_name:
    :return:
    """
    try:
        response = requests.get(f"{url}/{package_name}").json()
        return [semantic_version.Version(i) for i in response['versions'].keys()]
    except Exception as e:
        print("Could not get versions of package name. {e}")


def get_data_from_registry(package_name, version):
    data = requests.get(f"{url}/{package_name}/{version}").json()
    return data


def select_version(package, version) -> str:
    """
    This method simplifies the package name and returns a version to choose from the registry.
    :param package:
    :param version:
    :return:
    """
    # check version for ['latest', no operator and send straight without simplified]
    if version == 'latest':
        return version

    versions = get_versions(package_name=package)
    try:
        specs = semantic_version.NpmSpec(version)
    except ValueError:
        try:
            version = version.split(" ")
            specs = semantic_version.NpmSpec(version)
        except Exception as e:
            print("Could not parse version since wrong format of semVer. Using latest as version")
            # FIXME End case problem : '>= 1.5.0 < 2'. Add coerce or manual handling in this end case
            return 'latest'
    version = specs.select(versions)
    return version


def get_pk(package_name, version):
    return f"{package_name}_{version}"


def get_data(pk):
    return pk.split("_")


# async def handle_package_dependency(session, package_name, dependency_name, dependency_version):
#     """
#     This method gets a package name, dependency name, dependency version (unsimplified),, mark as visited in cache and publish update package task
#     :param session:
#     :param package_name:
#     :param dependency_name:
#     :param dependency_version:
#     :return:
#     """
#     # create dependency and add.
#     simplified_version_dependency = await fetch_version(package=dependency_name, version=dependency_version,
#                                                         session=session)
#     pk_dependency = get_pk(dependency_name, simplified_version_dependency)  # From simplified
#     dependency = await redis.get(pk_dependency)
#     print(f"Redis result is: {dependency}")
#     if dependency is None:
#         print(f"Inserting to redis visited value {pk_dependency}")
#         await redis.set(pk_dependency, -1)  # Updated, not jsoned.
#         # task = asyncio.create_task(update_package(dependency_name, simplified_dependency_version, session))
#
#         task = asyncio.create_task(update_package(dependency_name, dependency_version, session))
#         await task
#
#         # await queue.append((pk_dependency, path + [get_pk(package_name=package_name,
#         #                                                   version=simplified_dependency_version)]))  ## In other words - scan it. So scan
#     return pk_dependency

async def fetch_version(package, version, session) -> str:
    """
    This method simplifies the package name and returns a version to choose from the registry.
    :param package:
    :param version:
    :return:
    """
    # check version for ['latest', no operator and send straight without simplified]
    if version == 'latest':
        return version

    versions = await fetch_versions(package_name=package, session=session)
    try:
        specs = semantic_version.NpmSpec(version)
    except ValueError:
        try:
            version = version.split(" ")
            specs = semantic_version.NpmSpec(version)
        except Exception as e:
            print("Could not parse version since wrong format of semVer. Using latest as version")
            # FIXME End case problem : '>= 1.5.0 < 2'. Add coerce or manual handling in this end case
            return 'latest'
    version = specs.select(versions)
    return version


async def fetch_data_from_registry(package_name, version, session):
    """TODO:: Decorator?"""
    async with session.get(f"{url}/{package_name}/{version}") as response:
        data = await response.json()
        return data



def get_fetched_pk(package_name, version):
    return f"{get_pk(package_name=package_name, version=version)}_fetched"


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
    return version_simplified


async def update_package(package_name, version_name, session):
    """
    INV:: Fetch have been happened.
    :param package_name:
    :param version_name: version name (simplified) and latest
    :param session:
    :return:
    """
    before_fetch_data = time.time()
    data = await fetch_data_from_registry(package_name=package_name, version=version_name, session=session)
    print(F"{package_name} - FETCH DATA took {time.time() - before_fetch_data} seconds")
    if version_name == 'latest':
        version_name = data.get('version')
    start_time = time.time()
    print(f"Starting to update package: {package_name}")
    dependencies = data.get('dependencies', {})
    pk_current = get_pk(package_name=package_name, version=version_name)  # from simplified
    tasks = []
    for dependency_name, dependency_version in dependencies.items():
        version_simplified = await get_simplified_from_unsimplified(package_name=dependency_name,
                                                                    package_version=dependency_version,
                                                                    session=session)
        pk = get_pk(package_name=dependency_name, version=version_simplified)
        result_from_cache = await redis.get(pk)
        if result_from_cache is None:
            task = asyncio.create_task(update_package(dependency_name, version_simplified, session))
            tasks.append(task)
    dependency_ids = await asyncio.gather(*tasks)
    node_to_insert = {'dependencies': dependency_ids, 'name': package_name, 'version': str(version_name)}
    redis_time = time.time()
    await redis.set(pk_current, json.dumps(node_to_insert))
    print(
        f"UPDATE TIME for {package_name} took : {time.time() - start_time} and time to update redis took {time.time() - redis_time}")
    return pk_current


async def async_scan(package_name, version_name, session):
    print(f"Starting async scan for {package_name}:{version_name}")
    simplified_version = await get_simplified_from_unsimplified(package_name=package_name, package_version=version_name,
                                                                session=session)
    pk_pkg = get_pk(package_name=package_name, version=simplified_version)
    result_from_cache = await redis.get(pk_pkg)
    if result_from_cache is None:
        start_time = time.time()
        pk_pkg = await update_package(package_name, simplified_version, session)
        print(f"GET UPDATE PACKAGE TOOK {time.time() - start_time}")
    start_time = time.time()
    result = await get_json(pk_pkg)
    print(f"GET JSON TOOK {time.time() - start_time}")
    return result



original = {'express-3.7.2': {'dependencies': ['tornado-2.1.5'], 'name': 'express-3.7.2', 'last_updated': None},
            'tornado-2.1.5': [],
            'http-2.1.2': ['asyncio-1.1.2'],
            'asyncio-1.1.2': ['postgresql-9.6', 'requests-13.2.3'],
            'postgresql-9.6': ['cpp-0.2.9'],
            'requests-13.2.3': [],
            'cpp-0.2.9': []

            }

collection = []
# TODO:: DELETE ME
o = {'express-3.7.2': {
    'tornado-2.1.5': {},
    'http-2.1.2': {
        'asyncio-1.1.2': {
            'postgresql-9.6':
                {
                    'cpp-0.2.9'
                },
            'requests-13.2.3': {}
        },

    }
}}


async def get_json_from_node(id: str):
    """"""
    cached = await redis.get(id)  # Json with dependencies as k and values and dependencies
    if cached is not None:
        return json.loads(cached)
    return collection.get({'_id': id})


def get_json_pk(node_pk):
    return f"{node_pk}_json"


async def get_json(node_pk):
    result_from_redis = await redis.get(get_json_pk(node_pk))
    if result_from_redis is not None:
        json_to_return = await json.loads(result_from_redis)
        return json_to_return

    object = await get_json_from_node(node_pk)
    return {dependency_pk: await get_json(dependency_pk) for dependency_pk in object['dependencies']}
