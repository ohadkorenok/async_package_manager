import semantic_version
from fastapi import HTTPException
from app.settings import REGISTRY_URL as url
import logging

logger = logging.getLogger("package_manager")


async def fetch_versions(package_name: str, session):
    """
    Fetch all of the versions for a given package. We will use it mostly for handling `latest` versions since latest is
    relative. We want to save in our storage only simplified versions

    :param package_name: str represents package name
    :param session: Async session
    :return: version list of all of the versions there are, status code
    """
    async with session.get(f"{url}/{package_name}") as response:
        response, status = await response.json(), response.status
        result = [semantic_version.Version(i) for i in response.get('versions', {}).keys()]
        return result, status


async def fetch_version(package: str, version: str, session) -> str:
    """
    This method simplifies the package name and returns a version to choose from the registry.
    If latest - we just simplify the version and take it simplified as semver format using fetch data.
    For fetching the versions we first get an array of versions according to our semver expression and then choose using
    semantic_version the most suitable one.
    :param package:str represents package name
    :param version:str represents version in SemVer 2.0 format
    :param session: Async session
    :return: version in simplified format
    """
    if version == 'latest':
        data, status = await fetch_data_from_registry(package_name=package, version=version, session=session)
        if status != 200:
            logger.error(f"Exception in retrieving {package} and version {version}")
            raise HTTPException(detail=f"Exception in retrieving {package} and version {version}", status_code=status)
        return data.get('version')

    versions, status = await fetch_versions(package_name=package, session=session)
    if status != 200:
        logger.error(f"Exception in retrieving {package} and version {version}")
        raise HTTPException(detail=f"Exception in retrieving {package} and version {version}", status_code=status)
    try:
        specs = semantic_version.NpmSpec(version)
    except ValueError:
        try:
            version = version.split(" ")
            specs = semantic_version.NpmSpec(version)
        except Exception as e:
            logger.error("Could not parse version since wrong format of semVer. Using latest as version")
            return 'latest'
    version = specs.select(versions)
    return version


async def fetch_data_from_registry(package_name: str, version: str, session) -> tuple:
    """
    Fetch data from registry. Get all of the data on specific package and version
    :return: tuple of data and status
    """
    async with session.get(f"{url}/{package_name}/{version}") as response:
        data = await response.json()
        return data, response.status
