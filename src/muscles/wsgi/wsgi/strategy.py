from typing import Optional
import logging

from muscles.core import BaseStrategy
from watchdog.events import LoggingEventHandler
from .server import WsgiTransport, WsgiServer
from .error_handler import ResponseErrorHandler

event_handler = LoggingEventHandler()


class WsgiStrategy(BaseStrategy):
    """
    Стратегия WSGI сервера
    """
    def __init__(self):
        self._server = None
        self._server_key = None

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
        logger = kwargs.get('logger')
        container = kwargs.get('container')
        if logger is None and container is not None:
            logger = getattr(container, "logger", None)
        if isinstance(logger, str):
            logger = logging.getLogger(logger)
        if logger is None:
            logger = logging.getLogger("muscles.wsgi")
        debug = bool(kwargs.get('debug', False))

        server_key = (host, port, bool(debug), error_handler, id(logger))
        if self._server is None or self._server_key != server_key:
            self._server = WsgiServer(host, port, error_handler=error_handler, logger=logger, debug=debug)
            self._server_key = server_key
        server = self._server
        transport = kwargs.get('transport', WsgiTransport)
        server.init_transport(transport)
        return server.execute(*args, **kwargs)
