import semantic_version
import time

url = "https://registry.npmjs.org"


async def fetch_versions(package_name, session):
    start_time = time.time()
    async with session.get(f"{url}/{package_name}") as response:
        response = await response.json()
        result = [semantic_version.Version(i) for i in response['versions'].keys()]
        print(f"FETCH VERSIONS to {package_name} TOOK {time.time() - start_time}")
        return result


async def fetch_version(package, version, session) -> str:
    """
    This method simplifies the package name and returns a version to choose from the registry.
    :param package:
    :param version:
    :return:
    """
    start_time = time.time()

    # check version for ['latest', no operator and send straight without simplified]
    if version == 'latest':
        data = await fetch_data_from_registry(package_name=package, version=version, session=session)
        print(f"FETCH VERSION to {package} TOOK {time.time() - start_time}")

        return data.get('version')

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
    print(f"FETCH VERSION to {package} TOOK {time.time() - start_time}")

    return version


async def fetch_data_from_registry(package_name, version, session):
    """TODO:: Decorator?"""
    start_time = time.time()
    async with session.get(f"{url}/{package_name}/{version}") as response:
        data = await response.json()
        print(f"FETCH DATA FROM REGISTRY to {package_name} TOOK {time.time() - start_time}")
        return data
