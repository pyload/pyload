"""
Read more about conftest.py under: https://docs.pytest.org/en/stable/reference/fixtures.html
"""
import os
import pytest
import shutil

from pyload.core import Core


@pytest.fixture(scope="session")
def pyload_core():
    test_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(test_dir, ".pyload_test_data")
    try:
        # Return to clean state before running tests
        shutil.rmtree(test_data_dir)
    except FileNotFoundError:
        pass

    core = Core(userdir=test_data_dir, tempdir=f"{test_data_dir}/tmp", storagedir=None, debug=True, reset=None, dry=False, api_spec=False)
    yield core

@pytest.fixture(scope="session")
def api_key(pyload_core):
    return pyload_core.api.generate_apikey("pyload", "pyload")["data"]["key"]

@pytest.fixture(scope="session")
def app(pyload_core):
    app = pyload_core.webserver.app
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture(scope="session")
def client(app):
    return app.test_client()
