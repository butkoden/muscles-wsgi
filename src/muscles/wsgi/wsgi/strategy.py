from typing import Optional

from muscles.core import BaseStrategy
from watchdog.events import LoggingEventHandler
from .server import WsgiTransport, WsgiServer
from .error_handler import ResponseErrorHandler

event_handler = LoggingEventHandler()


class WsgiStrategy(BaseStrategy):
    """
    Стратегия WSGI сервера
    """

    def execute(self, *args, error_handler: Optional[ResponseErrorHandler] = None, **kwargs):
        """
        Запускаем обработку запросов
        :param args:
        :param error_handler:
        :param kwargs:
        :return:
        """
        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 8080)

        server = WsgiServer(host, port, error_handler=error_handler)
        transport = kwargs.get('transport', WsgiTransport)
        server.init_transport(transport)
        return server.execute(*args, **kwargs)
