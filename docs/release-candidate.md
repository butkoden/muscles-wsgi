# WSGI RC checklist

`muscles-wsgi` is released only after the core version range resolves from the
package index and the wheel imports without a sibling checkout.

```bash
PYTHONPATH=../muscles/src:src python -m pytest --import-mode=importlib -q
python -m build --wheel --sdist
```

The package tests cover request isolation, routing, templates, multipart,
OpenAPI, action projection and the WSGI test client. Gunicorn/uWSGI deployment
notes are in [production.md](production.md).
