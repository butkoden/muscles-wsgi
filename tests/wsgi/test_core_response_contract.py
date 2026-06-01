from muscles import HtmlResponse as CoreHtmlResponse
from muscles import JsonResponse as CoreJsonResponse
from muscles.wsgi.wsgi.response import BaseResponse as WsgiBaseResponse
from muscles.wsgi.wsgi.response import HtmlResponse as WsgiHtmlResponse
from muscles.wsgi.wsgi.response import JsonResponse as WsgiJsonResponse
from muscles.wsgi.wsgi.server import WsgiServer


def test_wsgi_server_accepts_core_json_response():
    server = WsgiServer(host="localhost", port=0, error_handler=Exception)
    response = server._to_protocol_response(CoreJsonResponse({"ok": True}))
    assert isinstance(response, WsgiJsonResponse)
    assert response.status == "200"
    assert response.make_body() == b'{"ok": true}'


def test_wsgi_server_accepts_core_html_response():
    server = WsgiServer(host="localhost", port=0, error_handler=Exception)
    response = server._to_protocol_response(CoreHtmlResponse("<h1>ok</h1>"))
    assert isinstance(response, WsgiHtmlResponse)
    assert response.status == "200"
    assert response.make_body() == b"<h1>ok</h1>"


def test_wsgi_server_keeps_legacy_protocol_response():
    server = WsgiServer(host="localhost", port=0, error_handler=Exception)
    legacy = WsgiBaseResponse(status=201, body={"created": True})
    response = server._to_protocol_response(legacy)
    assert response is legacy
