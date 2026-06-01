# Muscles WSGI Production Notes

## Run With Gunicorn

```bash
gunicorn app.application:app --bind 0.0.0.0:8080 --workers 2
```

## Run With uWSGI

```bash
uwsgi --http 0.0.0.0:8080 --wsgi-file app/application.py --callable app
```

## Reverse Proxy

Use nginx or equivalent to terminate TLS and proxy traffic to the WSGI server.
