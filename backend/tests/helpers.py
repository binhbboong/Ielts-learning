from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


def assert_all_routes_require_learner(app: FastAPI, exclude_prefixes=()) -> None:
    client = TestClient(app)
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if any(route.path.startswith(prefix) for prefix in exclude_prefixes):
            continue

        for method in route.methods - {"HEAD", "OPTIONS"}:
            response = client.request(method, route.path, json={})
            assert response.status_code == 401, (
                f"{method} {route.path} did not require authentication "
                f"(got {response.status_code})"
            )
