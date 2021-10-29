from app.utils import get_json, get_simplified_from_unsimplified, update_package, validate_if_updated, \
    simplify_and_update


async def async_scan(package_name, version_name, session):
    pk_pkg = await simplify_and_update(package_name, version_name, session)
    result = await get_json(pk_pkg)
    return result
