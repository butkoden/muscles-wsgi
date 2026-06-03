from muscles.wsgi.wsgi.strategy import WsgiStrategy


def test_wsgi_strategy_reuses_server_instance_between_requests():
    class DummyTransport:
        init_calls = 0

        def __init__(self):
            pass

        def init_server(self, server):
            DummyTransport.init_calls += 1
            self.server = server

        def execute(self, *args, **kwargs):
            return "ok"

    strategy = WsgiStrategy()
    first = strategy.execute(environ={}, start_response=lambda *a, **k: None, transport=DummyTransport)
    server_id_first = id(strategy._server)
    second = strategy.execute(environ={}, start_response=lambda *a, **k: None, transport=DummyTransport)
    server_id_second = id(strategy._server)

    assert first == "ok"
    assert second == "ok"
    assert server_id_first == server_id_second
    assert DummyTransport.init_calls == 1
