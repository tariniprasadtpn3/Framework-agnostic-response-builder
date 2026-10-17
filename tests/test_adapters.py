import datetime as dt
import json

import pytest


# --------------------------------------------------------------------- #
#  Django
# --------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def django_helper():
    pytest.importorskip("django")
    from django.conf import settings

    if not settings.configured:
        settings.configure(DEFAULT_CHARSET="utf-8")
    from response import DjangoResponseHelper

    return DjangoResponseHelper


def test_django_json(django_helper):
    res = django_helper.created({"id": 1}, location="/items/1")
    assert res.status_code == 201
    assert res["Location"] == "/items/1"
    assert json.loads(res.content)["data"] == {"id": 1}


def test_django_bodiless(django_helper):
    for res, code in ((django_helper.no_content(), 204), (django_helper.not_modified(), 304)):
        assert res.status_code == code
        assert res.content == b""


# --------------------------------------------------------------------- #
#  Flask
# --------------------------------------------------------------------- #
@pytest.fixture
def flask_helper():
    flask = pytest.importorskip("flask")
    from response import FlaskResponseHelper

    with flask.Flask(__name__).app_context():
        yield FlaskResponseHelper


def test_flask_json(flask_helper):
    res = flask_helper.found("/login")
    assert res.status_code == 302
    assert res.headers["Location"] == "/login"
    assert res.get_json()["status"] == 302


def test_flask_bodiless(flask_helper):
    for res, code in ((flask_helper.no_content(), 204), (flask_helper.not_modified(), 304)):
        assert res.status_code == code
        assert res.get_data() == b""


# --------------------------------------------------------------------- #
#  FastAPI — through a real ASGI client so protocol errors would surface
# --------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def fastapi_client():
    fastapi = pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from response import FastAPIResponseHelper as R

    app = fastapi.FastAPI()
    app.get("/ok")(lambda: R.ok({"when": dt.datetime(2026, 1, 2, 3, 4, 5)}))
    app.get("/empty")(lambda: R.no_content())
    app.get("/cached")(lambda: R.not_modified(headers={"ETag": '"v1"'}))
    app.get("/moved")(lambda: R.moved_permanently("/new"))
    return TestClient(app, follow_redirects=False)


def test_fastapi_encodes_datetime(fastapi_client):
    res = fastapi_client.get("/ok")
    assert res.status_code == 200
    assert res.json()["data"] == {"when": "2026-01-02T03:04:05"}


def test_fastapi_bodiless(fastapi_client):
    res = fastapi_client.get("/empty")
    assert res.status_code == 204
    assert res.content == b""
    res = fastapi_client.get("/cached")
    assert res.status_code == 304
    assert res.headers["ETag"] == '"v1"'


def test_fastapi_redirect(fastapi_client):
    res = fastapi_client.get("/moved")
    assert res.status_code == 301
    assert res.headers["Location"] == "/new"
