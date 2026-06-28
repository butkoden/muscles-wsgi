from muscles.wsgi import MuscularWsgiApp, wsgi_app


def test_wsgi_app_entrypoint_exports_callable():
    app = MuscularWsgiApp()
    application = wsgi_app(app)
    assert callable(application)


def test_wsgi_app_passes_request_state_via_execute_kwargs():
    captured = {}

    class DummyContext:
        def execute(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return [b"ok"]

    class DummyApp:
        wsgi = DummyContext()

    application = wsgi_app(DummyApp())
    environ = {"PATH_INFO": "/health"}

    def start_response(status, headers):
        return None

    result = application(environ, start_response)

    assert result == [b"ok"]
    assert captured["args"] == ()
    assert captured["kwargs"]["environ"] is environ
    assert captured["kwargs"]["start_response"] is start_response
