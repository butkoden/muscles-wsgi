import importlib.util


def test_wsgi_schema_duplicate_package_is_removed():
    assert importlib.util.find_spec("muscles.wsgi.schema_") is None
