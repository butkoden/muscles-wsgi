from muscles.wsgi.testing import TestClient


def app(environ, start_response):
    body = environ["wsgi.input"].read()
    start_response("201 Created", [("Content-Type", "application/json")])
    return [
        b'{"path":"%b","auth":"%b","body":%b}' % (
            environ["PATH_INFO"].encode(),
            environ.get("HTTP_AUTHORIZATION", "").encode(),
            body or b"null",
        )
    ]


def test_wsgi_test_client_sends_json_and_bearer_auth():
    client = TestClient(app).with_bearer("token")

    response = client.post("/api/documents?x=1", json={"title": "Spec"})

    assert response.status_code == 201
    assert response.json()["path"] == "/api/documents"
    assert response.json()["auth"] == "Bearer token"
    assert response.json()["body"] == {"title": "Spec"}
