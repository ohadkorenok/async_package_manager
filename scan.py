from utils import get_pk, get_json, redis, get_simplified_from_unsimplified, update_package


# from tasks import update_package_from_main_package


async def async_scan(package_name, version_name, session):
    print(f"Starting async scan for {package_name}:{version_name}")
    simplified_version = await get_simplified_from_unsimplified(package_name=package_name, package_version=version_name,
                                                                session=session)
    pk_pkg = get_pk(package_name=package_name, version=simplified_version)
    result_from_cache = await redis.get(pk_pkg)
    if result_from_cache is None:
        pk_pkg = await update_package(package_name, simplified_version, session)
        # pk_pkg_task_result = update_package_from_main_package.delay(package_name, simplified_version)
        # pk_pkg = pk_pkg_task_result.get()
    result = await get_json(pk_pkg)
    return result
