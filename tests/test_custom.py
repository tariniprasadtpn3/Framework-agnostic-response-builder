import pytest

from response import HttpStatus, JsonResponseHelper, PlainResponseHelper, custom_response


class AppResponse(PlainResponseHelper):
    messages = {404: "Nothing here", HttpStatus.FORBIDDEN: "No entry"}

    user_not_found = custom_response(HttpStatus.NOT_FOUND, "User not found", internal_code=40401)
    order_placed = custom_response(201, "Order placed", internal_code=20101)
    rate_limited = custom_response(429, internal_code=42901, headers={"Retry-After": "30"})
    validation_failed = custom_response(422, "Validation failed")


class AdminResponse(AppResponse):
    messages = {403: "Admins only"}

    admin_required = custom_response(403, internal_code=40399)


def test_custom_response_defaults():
    res = AppResponse.user_not_found()
    assert res.status_code == 404
    assert res.body == {"status": 40401, "message": "User not found", "data": []}


def test_custom_response_overrides():
    res = AppResponse.order_placed(data={"id": 9}, trace_id="t-1", message="Done",
                                   headers={"Location": "/orders/9"})
    assert res.status_code == 201
    assert res.body == {"status": 20101, "message": "Done", "data": {"id": 9}, "trace_id": "t-1"}
    assert res.headers == {"Location": "/orders/9"}


def test_custom_response_headers_merge():
    res = AppResponse.rate_limited(headers={"X-Limit": "100"})
    assert res.headers == {"Retry-After": "30", "X-Limit": "100"}
    assert res.body["message"] == "Too Many Requests"


def test_custom_response_is_keyword_only():
    with pytest.raises(TypeError):
        AppResponse.order_placed({"id": 9})


def test_custom_response_metadata():
    assert AppResponse.user_not_found.__name__ == "user_not_found"
    assert AppResponse.user_not_found.__doc__ == "404 — User not found"


def test_message_overrides_apply_to_builtin_methods():
    assert AppResponse.not_found().body["message"] == "Nothing here"
    assert AppResponse.forbidden().body["message"] == "No entry"
    assert AppResponse.not_found("Explicit wins").body["message"] == "Explicit wins"


def test_message_overrides_are_inherited_and_merged():
    assert AdminResponse.not_found().body["message"] == "Nothing here"
    assert AdminResponse.forbidden().body["message"] == "Admins only"
    assert AdminResponse.admin_required().body == {"status": 40399, "message": "Admins only", "data": []}
    assert AdminResponse.user_not_found().status_code == 404


def test_overrides_do_not_leak_to_base_helpers():
    assert PlainResponseHelper.not_found().body["message"] == "Requested Resource Not Found"
    assert JsonResponseHelper.messages == {}


def test_custom_response_on_auto_helper(monkeypatch):
    # Other tests may have imported a framework in this process; pin the adapter.
    monkeypatch.setenv("RESPONSE_BUILDER_FRAMEWORK", "plain")

    class Api(JsonResponseHelper):
        payment_required = custom_response(402, internal_code=40201)

    res = Api.payment_required()
    assert res.status_code == 402
    assert res.body == {"status": 40201, "message": "Payment Required", "data": []}


def test_build_accepts_any_int_status():
    res = PlainResponseHelper.build(418)
    assert res.body["message"] == "I'm a Teapot"
    assert PlainResponseHelper.build(299).body["message"] == "Unknown Status"
    assert PlainResponseHelper.build(299).body["data"] == {}


def test_build_rejects_invalid_status():
    with pytest.raises(ValueError):
        PlainResponseHelper.build(700)


def test_new_builtin_methods():
    assert PlainResponseHelper.unprocessable_entity(errors=[{"field": "email"}]).status_code == 422
    res = PlainResponseHelper.too_many_requests(retry_after=60)
    assert res.status_code == 429
    assert res.headers == {"Retry-After": "60"}
