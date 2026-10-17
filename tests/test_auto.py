"""
Auto-detection depends on what's in sys.modules, so each scenario runs in a
fresh interpreter.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def run(code, env=None):
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, **(env or {})},
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def needs(*modules):
    for module in modules:
        pytest.importorskip(module)


def test_plain_when_no_framework_loaded():
    out = run("""
        import sys
        from response import JsonResponseHelper as R
        res = R.ok({"a": 1})
        print(type(res).__name__, res.status_code, {"django", "flask", "fastapi"} & set(sys.modules))
    """)
    assert out == "PlainResponse 200 set()"


def test_flask_inside_app_context():
    needs("flask")
    out = run("""
        import flask
        from response import JsonResponseHelper as R
        app = flask.Flask(__name__)
        with app.test_request_context():
            res = R.created({"id": 1}, location="/items/1")
            print(type(res).__module__.split(".")[0], res.status_code, res.headers["Location"])
    """)
    assert out == "flask 201 /items/1"


def test_flask_outside_app_context_falls_back_to_plain():
    needs("flask")
    out = run("""
        import flask
        from response import JsonResponseHelper as R
        print(type(R.ok()).__name__)
    """)
    assert out == "PlainResponse"


def test_fastapi_route():
    needs("fastapi", "httpx")
    out = run("""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from response import JsonResponseHelper as R
        app = FastAPI()
        app.get("/")(lambda: R.not_found("nope"))
        app.get("/empty")(lambda: R.no_content())
        client = TestClient(app)
        res = client.get("/")
        print(res.status_code, res.json()["message"], client.get("/empty").status_code)
    """)
    assert out == "404 nope 204"


def test_django_configured():
    needs("django")
    out = run("""
        from django.conf import settings
        settings.configure()
        from response import JsonResponseHelper as R
        res = R.bad_request("bad")
        print(type(res).__name__, res.status_code)
    """)
    assert out == "JsonResponse 400"


def test_fastapi_wins_over_django_orm():
    needs("fastapi", "django")
    out = run("""
        from django.conf import settings
        settings.configure()
        import fastapi
        from response import detect_framework
        print(detect_framework())
    """)
    assert out == "fastapi"


def test_configure_overrides_detection():
    needs("fastapi")
    out = run("""
        import fastapi
        import response
        response.configure("plain")
        a = response.detect_framework()
        response.configure(None)
        print(a, response.detect_framework())
    """)
    assert out == "plain fastapi"


def test_env_var_overrides_detection():
    needs("fastapi")
    out = run("""
        import fastapi
        from response import detect_framework
        print(detect_framework())
    """, env={"RESPONSE_BUILDER_FRAMEWORK": "Plain"})
    assert out == "plain"


def test_unknown_framework_rejected():
    from response import configure

    with pytest.raises(ValueError):
        configure("tornado")
