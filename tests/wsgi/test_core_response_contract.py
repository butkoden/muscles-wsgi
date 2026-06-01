from muscles import HtmlResponse as CoreHtmlResponse
from muscles import BaseResponse as CoreBaseResponse
from muscles import JsonResponse as CoreJsonResponse
from muscles.wsgi.wsgi.response import BaseResponse as WsgiBaseResponse
from muscles.wsgi.wsgi.server import WsgiServer


def test_wsgi_server_accepts_core_json_response():
    server = WsgiServer(host="localhost", port=0, error_handler=Exception)
    response = server._to_protocol_response(CoreJsonResponse({"ok": True}))
    assert isinstance(response, WsgiBaseResponse)
    assert response.status == "200"
    assert response.make_body() == b'{"ok": true}'


def test_wsgi_server_accepts_core_html_response():
    server = WsgiServer(host="localhost", port=0, error_handler=Exception)
    response = server._to_protocol_response(CoreHtmlResponse("<h1>ok</h1>"))
    assert isinstance(response, WsgiBaseResponse)
    assert response.status == "200"
    assert response.make_body() == b"<h1>ok</h1>"


def test_wsgi_server_keeps_legacy_protocol_response():
    server = WsgiServer(host="localhost", port=0, error_handler=Exception)
    legacy = WsgiBaseResponse(status=201, body={"created": True})
    response = server._to_protocol_response(legacy)
    assert response is legacy


def test_wsgi_server_keeps_legacy_serialization_for_non_json_serializable_objects():
    class DummyFieldStorage:
        def __str__(self):
            return "FieldStorage('name', 'Denis')"

    server = WsgiServer(host="localhost", port=0, error_handler=Exception)
    response = server._to_protocol_response({"field": DummyFieldStorage()})
    payload = response.make_body()
    assert b"FieldStorage('name', 'Denis')" in payload


def test_wsgi_server_preserves_core_custom_content_type():
    server = WsgiServer(host="localhost", port=0, error_handler=Exception)
    core = CoreBaseResponse(
        body=b'{"type":"problem"}',
        status=422,
        headers={"X-Trace-Id": "abc"},
        content_type="application/problem+json",
    )
    response = server._to_protocol_response(core)
    headers = dict(response.headers)
    assert headers["Content-Type"] == "application/problem+json"
    assert headers["X-Trace-Id"] == "abc"
