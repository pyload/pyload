import socket

import flask
import pytest

from pyload.core.api import (
    Api,
    Role,
    _resolve_public_fetch_targets,
    method_map,
    perm_map,
)
from pyload.webui.app.blueprints.cnl_blueprint import bp as cnl_bp
from pyload.webui.app.blueprints.json_blueprint import bp as json_bp
from pyload.webui.app.extensions import csrf
from pyload.webui.app.helpers import is_loopback_request


class DummyRequest:
    def __init__(self, remote_addr, headers=None):
        self.remote_addr = remote_addr
        self.headers = headers or {}


class DummyApi:
    def user_exists(self, user):
        return bool(user)

    def get_config_value(self, *args):
        if args == ("ClickNLoad", "enabled", "plugin"):
            return True
        return None

    def order_package(self, pid, pos):
        self.ordered_package = (pid, pos)

    def stop_downloads(self, ids):
        self.stopped_downloads = ids

    def order_file(self, fid, pos):
        self.ordered_file = (fid, pos)

    def move_package(self, dest, package_id):
        self.moved_package = (dest, package_id)


@pytest.fixture
def web_client():
    app = flask.Flask(__name__)
    app.secret_key = "test-secret"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["PYLOAD_API"] = DummyApi()
    csrf.init_app(app)
    app.register_blueprint(json_bp)
    app.register_blueprint(cnl_bp)
    return app.test_client()


def test_is_loopback_request_accepts_direct_loopback():
    assert is_loopback_request(DummyRequest("127.0.0.1")) is True
    assert is_loopback_request(DummyRequest("::1")) is True


def test_is_loopback_request_rejects_forwarded_requests():
    request = DummyRequest("127.0.0.1", headers={"X-Forwarded-For": "203.0.113.9"})
    assert is_loopback_request(request) is False


def test_service_call_is_admin_only():
    api = object.__new__(Api)

    assert "service_call" not in perm_map
    assert (
        api.is_authorized("service_call", {"role": Role.ADMIN, "permission": 0}) is True
    )
    assert (
        api.is_authorized("service_call", {"role": Role.USER, "permission": 0}) is False
    )
    assert method_map["service_call"] == "POST"


def test_resolve_public_fetch_targets_rejects_private_addresses(monkeypatch):
    def fake_getaddrinfo(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    with pytest.raises(ValueError, match="local or reserved"):
        _resolve_public_fetch_targets("http://example.com")


def test_resolve_public_fetch_targets_returns_public_addresses(monkeypatch):
    def fake_getaddrinfo(host, port, type):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    assert _resolve_public_fetch_targets("http://example.com") == ["93.184.216.34"]


def test_parse_urls_uses_resolved_addresses_without_proxy(monkeypatch):
    api = object.__new__(Api)
    captured = {}

    def fake_check_urls(urls):
        return {"links": urls}

    def fake_get_url(url, redirect=False, request_options=None):
        captured["url"] = url
        captured["redirect"] = redirect
        captured["request_options"] = request_options
        return "https://files.example.test/download"

    monkeypatch.setattr(
        "pyload.core.api._resolve_public_fetch_targets",
        lambda url: ["93.184.216.34"],
    )
    monkeypatch.setattr("pyload.core.api.get_url", fake_get_url)
    monkeypatch.setattr(api, "check_urls", fake_check_urls)

    result = api.parse_urls(url="http://example.com")

    assert result == {"links": ["https://files.example.test/download"]}
    assert captured["redirect"] is False
    assert captured["request_options"] == {
        "proxies": {},
        "resolved_addresses": ["93.184.216.34"],
    }


def test_json_mutating_routes_reject_get(web_client):
    routes = [
        "/json/package_order",
        "/json/abort_link",
        "/json/link_order",
        "/json/move_package",
    ]

    for route in routes:
        response = web_client.get(route)
        assert response.status_code == 405


def test_json_mutating_routes_accept_post_when_authenticated(web_client):
    with web_client.session_transaction() as session:
        session.update(
            {
                "authenticated": True,
                "name": "tester",
                "role": Role.ADMIN,
                "perms": 0,
            }
        )

    assert (
        web_client.post("/json/package_order", data={"pid": 7, "pos": 2}).status_code
        == 200
    )
    assert web_client.post("/json/abort_link", data={"id": 11}).status_code == 200
    assert (
        web_client.post("/json/link_order", data={"fid": 13, "pos": 3}).status_code
        == 200
    )
    assert (
        web_client.post("/json/move_package", data={"id": 17, "dest": 1}).status_code
        == 200
    )


def test_clicknload_route_requires_direct_loopback(web_client):
    allowed = web_client.get("/flash/", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    blocked = web_client.get(
        "/flash/",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        headers={"X-Forwarded-For": "198.51.100.7"},
    )

    assert allowed.status_code == 200
    assert blocked.status_code == 403
