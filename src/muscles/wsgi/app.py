from __future__ import annotations

from muscles import ApplicationMeta, Configurator, Context
from .wsgi import WsgiStrategy


class MuscularWsgiApp(metaclass=ApplicationMeta):
    """
    Minimal WSGI-oriented Muscles application skeleton.
    Projects can subclass this class and register routes/controllers in app code.
    """

    package_paths = []
    shutup = False

    config = Configurator(
        obj={
            "main": {
                "BASEDIR": ".",
                "BASE_URL": "http://localhost:8080",
                "SERVER_NAME": "localhost:8080",
                "HOST": "0.0.0.0",
                "PORT": "8080",
                "ENV": "development",
                "DEBUG": True,
                "TIMEZONE": "UTC",
                "MAIN_ROUTE": "page.index",
            },
            "routes": {"prefix": ""},
            "api": {"prefix": "/api", "default_version": "v1", "controllers": {}},
        }
    )

    wsgi = Context(WsgiStrategy, params={})

    def run(self, *args, **kwargs):
        return self.wsgi.execute(*args, **kwargs, shutup=self.shutup)


def wsgi_app(app: MuscularWsgiApp, context: str | Context | None = None):
    def _resolve_context():
        if isinstance(context, Context):
            return context
        if context is not None and hasattr(app, context):
            selected = getattr(app, context)
            if not isinstance(selected, Context):
                raise TypeError(f"Application has no context '{context}'")
            return selected
        if hasattr(app, 'wsgi'):
            return getattr(app, 'wsgi')
        raise TypeError("Application has no context 'wsgi'")

    def application(environ, start_response):
        ctx = _resolve_context()
        return ctx.execute(environ=environ, start_response=start_response)

    return application
