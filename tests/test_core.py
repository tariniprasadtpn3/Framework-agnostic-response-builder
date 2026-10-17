import subprocess
from pathlib import Path
import sys

import pytest

from response import ExceptionInfo, HttpStatus, PlainResponseHelper as R, ResponseSchema


def test_ok_envelope():
    res = R.ok({"id": 1}, metadata={"page": 1}, trace_id="t-1")
    assert res.status_code == 200
    assert res.body == {
        "status": 200,
        "message": "Success",
        "data": {"id": 1},
        "metadata": {"page": 1},
        "trace_id": "t-1",
    }
    assert res.headers == {}


def test_ok_internal_code_and_custom_message():
    res = R.ok([1], "Fetched", internal_code=2001)
    assert res.body["status"] == 2001
    assert res.body["message"] == "Fetched"


def test_default_data_shape():
    assert R.ok().body["data"] == {}
    assert R.not_found().body["data"] == []


def test_falsy_data_is_preserved():
    assert R.ok(0).body["data"] == 0
    assert R.ok([]).body["data"] == []


def test_error_envelope():
    res = R.bad_request("Bad sort", errors=[{"field": "sort"}])
    assert res.status_code == 400
    assert res.body == {
        "status": 400,
        "message": "Bad sort",
        "data": [],
        "errors": [{"field": "sort"}],
    }


@pytest.mark.parametrize("method, code", [
    ("unauthorized", 401), ("forbidden", 403), ("not_found", 404),
    ("method_not_allowed", 405), ("request_timeout", 408), ("conflict", 409),
    ("internal_server_error", 500), ("not_implemented", 501), ("bad_gateway", 502),
    ("service_unavailable", 503), ("gateway_timeout", 504),
])
def test_error_methods_use_default_message(method, code):
    res = getattr(R, method)()
    assert res.status_code == code
    assert res.body["message"] == HttpStatus(code).message


@pytest.mark.parametrize("res, code", [
    (R.no_content(), 204),
    (R.not_modified(headers={"ETag": '"v1"'}), 304),
    (R.build(HttpStatus.NO_CONTENT, "ignored", data={"x": 1}), 204),
])
def test_bodiless_statuses(res, code):
    assert res.status_code == code
    assert res.body is None


def test_not_modified_keeps_headers():
    assert R.not_modified(headers={"ETag": '"v1"'}).headers == {"ETag": '"v1"'}


def test_redirects_set_location():
    assert R.found("/login").headers == {"Location": "/login"}
    res = R.moved_permanently("/new")
    assert res.status_code == 301
    assert res.headers == {"Location": "/new"}


def test_created_location_is_optional():
    assert R.created({"id": 7}).headers == {}
    assert R.created({"id": 7}, location="/items/7").headers == {"Location": "/items/7"}


def test_schema_copies_caller_containers():
    metadata = {"page": 1}
    schema = ResponseSchema(HttpStatus.OK, "Success", 200, metadata=metadata)
    metadata["page"] = 2
    assert schema.to_dict()["metadata"] == {"page": 1}


def _raise_value_error():
    raise ValueError("boom")  # line asserted below


def test_exception_info_points_at_raise_site():
    try:
        _raise_value_error()
    except ValueError:
        info = ExceptionInfo.capture()
    assert info.filename == "test_core.py"
    assert info.line_number == _raise_value_error.__code__.co_firstlineno + 1
    assert info.detail == "boom"


def test_exception_info_from_explicit_exception():
    try:
        _raise_value_error()
    except ValueError as exc:
        caught = exc
    info = ExceptionInfo.capture(caught)
    assert info.exc_type is ValueError
    assert info.line_number == _raise_value_error.__code__.co_firstlineno + 1


def test_exception_info_hides_internals_by_default():
    info = ExceptionInfo(ValueError, "db.py", 10, "password=secret")
    assert info.to_error_dict() == {"type": "ValueError"}
    assert info.to_error_dict(include_debug=True)["detail"] == "password=secret"


def test_import_does_not_load_frameworks():
    code = (
        "import sys, response; "
        "from response import *; "
        "loaded = {'django', 'flask', 'fastapi'} & set(sys.modules); "
        "assert not loaded, loaded"
    )
    subprocess.run([sys.executable, "-c", code], check=True, cwd=Path(__file__).parents[1])
