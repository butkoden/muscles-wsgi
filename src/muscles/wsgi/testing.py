from __future__ import annotations

import io
import json
import uuid
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass
class TestResponse:
    status_code: int
    headers: dict[str, str]
    content: bytes

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")

    def json(self):
        return json.loads(self.text)


class TestClient:
    __test__ = False

    def __init__(self, app, headers: dict[str, str] | None = None):
        self.app = app
        self.headers = headers or {}

    def with_bearer(self, token: str) -> "TestClient":
        headers = dict(self.headers)
        headers["Authorization"] = f"Bearer {token}"
        return TestClient(self.app, headers=headers)

    def get(self, path: str, **kwargs) -> TestResponse:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> TestResponse:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs) -> TestResponse:
        return self.request("PATCH", path, **kwargs)

    def put(self, path: str, **kwargs) -> TestResponse:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> TestResponse:
        return self.request("DELETE", path, **kwargs)

    def request(
        self,
        method: str,
        path: str,
        json: object | None = None,
        data: bytes | str | dict | None = None,
        headers: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> TestResponse:
        parsed = urlsplit(path)
        request_headers = dict(self.headers)
        request_headers.update(headers or {})
        body = b""

        if files:
            boundary = f"----muscles-{uuid.uuid4().hex}"
            request_headers.setdefault("Content-Type", f"multipart/form-data; boundary={boundary}")
            body = self._encode_multipart(boundary, files, data)
        elif json is not None:
            request_headers.setdefault("Content-Type", "application/json")
            body = __import__("json").dumps(json).encode("utf-8")
        elif data is not None:
            body = data.encode("utf-8") if isinstance(data, str) else data

        request_headers.setdefault("Content-Length", str(len(body)))
        environ = self._build_environ(method, parsed, request_headers, body)
        captured = {}

        def start_response(status, response_headers, exc_info=None):
            captured["status"] = status
            captured["headers"] = response_headers

        result = self.app(environ, start_response)
        chunks = []
        if result is not None:
            for chunk in result:
                chunks.append(chunk.encode("utf-8") if isinstance(chunk, str) else chunk)
            close = getattr(result, "close", None)
            if close:
                close()

        status = captured.get("status", "500 Internal Server Error")
        response_headers = {
            key.title(): value
            for key, value in captured.get("headers", [])
        }
        return TestResponse(status_code=int(str(status).split(" ", 1)[0]), headers=response_headers, content=b"".join(chunks))

    def _build_environ(self, method, parsed, headers, body):
        path = parsed.path or "/"
        environ = {
            "REQUEST_METHOD": method.upper(),
            "SCRIPT_NAME": "",
            "PATH_INFO": path,
            "QUERY_STRING": parsed.query,
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": parsed.scheme or "http",
            "wsgi.input": io.BytesIO(body),
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "SERVER_NAME": parsed.hostname or "testserver",
            "SERVER_PORT": str(parsed.port or 80),
            "REMOTE_ADDR": "127.0.0.1",
        }
        for key, value in headers.items():
            normalized = key.upper().replace("-", "_")
            if normalized == "CONTENT_TYPE":
                environ["CONTENT_TYPE"] = str(value)
            elif normalized == "CONTENT_LENGTH":
                environ["CONTENT_LENGTH"] = str(value)
            else:
                environ[f"HTTP_{normalized}"] = str(value)
        return environ

    def _encode_multipart(self, boundary, files, data):
        chunks = []
        fields = data if isinstance(data, dict) else {}
        for name, value in fields.items():
            chunks.extend([
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                str(value).encode(),
                b"\r\n",
            ])
        for name, file_data in files.items():
            filename, payload, content_type = file_data
            chunks.extend([
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                payload,
                b"\r\n",
            ])
        chunks.append(f"--{boundary}--\r\n".encode())
        return b"".join(chunks)
