from fastapi import Depends, FastAPI

from app.core.security import require_learner
from tests.helpers import assert_all_routes_require_learner


def _fully_protected_app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(require_learner)])
    def protected():
        return {"ok": True}

    return app


def _partially_protected_app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(require_learner)])
    def protected():
        return {"ok": True}

    @app.get("/unprotected")
    def unprotected():
        return {"ok": True}

    return app


def test_passes_when_every_route_requires_learner():
    assert_all_routes_require_learner(_fully_protected_app())


def test_fails_when_a_route_does_not_require_learner():
    try:
        assert_all_routes_require_learner(_partially_protected_app())
    except AssertionError:
        return
    raise AssertionError(
        "expected assert_all_routes_require_learner to raise for an unprotected route"
    )


def test_excludes_routes_under_excluded_prefixes():
    app = FastAPI()

    @app.post("/api/auth/login")
    def login():
        return {"ok": True}

    assert_all_routes_require_learner(app, exclude_prefixes=["/api/auth"])
