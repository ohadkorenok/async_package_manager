from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from app.main import app, redis

FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


def test_read_accepts():
    packages_and_results = {
        "/async/2.0.1": {
            "lodash_4.17.21": {}
        },
        "/lodash/4.17.21": {},
        "mime-types/2.0.1": {
            "mime-db_1.0.3": {}
        },
        "/mime-db/1.0.3": {},
        "/accepts/1.3.7": {
            "mime-types_2.1.33": {
                "mime-db_1.50.0": {}
            },
            "negotiator_0.6.2": {}
        },
        "/negotiator/0.6.2": {},

    }
    problematic_packages_and_responses = {
        'yahooooooooofasa/2.17': {'json': {
            "detail": "Exception in retrieving yahooooooooofasa and version 2.17"
        }, 'status': 404},
        'plapslplsd/latest': {'json': {
            "detail": "Exception in retrieving plapslplsd and version latest"
        }, 'status': 404}

    }
    with TestClient(app) as client:
        for url, val in packages_and_results.items():
            response = client.get(url)
            assert response.status_code == 200
            assert response.json() == val
        for url, val in problematic_packages_and_responses.items():
            response = client.get(url)
            assert response.status_code == val['status']
            assert response.json() == val['json']
