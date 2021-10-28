import requests
import semantic_version
import asyncio
import aioredis
from settings import cache_url
import json
from fastapi import BackgroundTasks, FastAPI

redis = aioredis.from_url(cache_url)
# await redis.set("my-key", "value")
# value = await redis.get("my-key")

url = "https://registry.npmjs.org"


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

async def fetch_version_and_data(package_name, version_name, session):
    simplified_version = await fetch_version(package=package_name, version=version_name, session=session)
    data = await fetch_data_from_registry(package_name=package_name, version=simplified_version, session=session)
    return data


async def update_if_necessary(pkg_name, pkg_version, session):
    fetch_version_task = asyncio.create_task(
        fetch_version_and_data(package_name=pkg_name, version_name=pkg_version,
                               session=session))
    data = await fetch_version_task  ## Version is now simplified
    pkg_version_simplified = data.get('version')
    pk = get_pk(package_name=pkg_name, version=pkg_version_simplified)
    print(f"dependency pk is:{pk}")
    result_from_cache = await redis.get(pk)
    if result_from_cache is None:
        task = asyncio.create_task(update_package(pkg_name, pkg_version_simplified, data, session))
        return task


async def update_package(package_name, version_name, data, session):
    """
    :param package_name:
    :param version_name: version name (simplified)
    :param session:
    :return:
    """
    print(f"Starting to update package: {package_name}")
    dependencies = data.get('dependencies', {})
    pk_current = get_pk(package_name=package_name, version=version_name)  # from simplified

    # GET DEPENDENCY OBJECT #
    # curr_version = Dependencies.objects.get_or_create(pk_current) # IN ASYNC : Write get or create async easily.

    # open async tasks
    tasks = []
    for dependency_name, dependency_version in dependencies.items():
        task = await update_if_necessary(dependency_name, dependency_version, session)
        tasks.append(task)
    dependency_ids = await asyncio.gather(*tasks)
    node_to_insert = {'dependencies': dependency_ids, 'name': package_name, 'version': str(version_name)}
    print(f"inserting node: {node_to_insert} into redis")
    await redis.set(pk_current, json.dumps(node_to_insert))
    return pk_current


async def async_scan(package_name, version_name, session):
    print(f"Starting async scan for {package_name}:{version_name}")
    # simplified_version = await fetch_version(package_name, version=version_name, session=session)
    pk_package_task = await update_if_necessary(package_name, version_name, session)
    pk_package = await pk_package_task
    print(f"pk_package_task is {pk_package_task}")

    # pk_package = await update_package(package_name=package_name, version_name=simplified_version, session=session)
    return await get_json(pk_package_task)


def bfs(visited, node, queue):
    # Inserting worker task
    # Visited will map the values for
    node_pk_name = get_pk(package_name=node['package_name'], version=node['version_name'])
    visited.add(node_pk_name)
    queue.append((node_pk_name, []))
    #
    while queue:
        # Processing worker task
        curr, path = queue.pop(0)  # Version package and name
        package_name, version_name = get_data(curr)
        simplified_version = select_version(package=package_name, version=version_name)  # get specific version
        data = get_data_from_registry(package_name=package_name, version=simplified_version)
        dependencies = data.get('dependencies', {})
        if version_name == 'latest':
            simplified_version = data['version']
        pk_current = get_pk(package_name=package_name, version=simplified_version)
        # print(f"Scanning {pk_current}")
        # GET DEPENDENCY OBJECT #
        # curr_version = Dependencies.objects.get_or_create(pk_current)

        for dependency_name, dependency_version in dependencies.items():
            # create dependency and add.
            simplified_dependency_version = select_version(package=dependency_name, version=dependency_version)
            pk_dependency = get_pk(dependency_name, simplified_dependency_version)
            # dep_pk = Dependncy.get_or_create(pk_dependency, defaults = version_name, package_name)[0].pk_name
            # curr_version.add(dep_pk)

            if pk_dependency not in visited:
                visited.add(pk_dependency)
                queue.append((pk_dependency, path + [get_pk(package_name=package_name, version=simplified_version)]))

        # Insert to dependency table all of the dependencies with the simplified versions
        # Dependencies.objects.update_or_create(pk_name)


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


# dependency: \
#     name(key)
#     dependencies: dependency[]

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
    print(f"{node_pk} is : {object}")
    return {dependency_pk: await get_json(dependency_pk) for dependency_pk in object['dependencies']}
    # for dependency_pk in object['dependencies']:
    #     return {dependency_pk: get_json(dependency_pk)}


# def get_json(dependency_object: list):
#     # pk_name = get_pk_name(dependency_object) #
#     # if pk_name in cache:
#     #     return cache.get(pk_name)
#     ## Get from DB IF TIME VALIDATION ALLOWS SO. ONLY ELSE:
#     result = {}
#     for dep in dependency_object:
#         result[dep] = get_json(dep)
#     # cache[pk_name].insert(result) # Cache Update
#     # dep_object.update(json=result) # DB Update
#     return result


def view(package, version):  # TODO:: Latest!

    visited = set()  # TODO:: Change to cache
    queue = []
    bfs(visited, {'package_name': package, 'version_name': version}, queue)

    # simplified_version = select_version(package=package, version=version)
    # for dependency_name, dependency_version in get_dependencies(package_name=package, version=simplified_version):
    #     simplified_dep_version = select_version(package=dependency_name, version=dependency_version)
    #     for dependency_name, dependency_version in get_dependencies(dependency_name, simplified_dep_version).items():
    #         # TODO:: check whether we have to use this function inside a worker.
    #         pass
    return queue

# package_name_from_input = "express/latest".split("/")
# # package_name_from_input = "http-errors/1.7.2".split("/")
# # package_name_from_input = "async/>=2.0.1".split("/")
# ohad = view(*package_name_from_input)
