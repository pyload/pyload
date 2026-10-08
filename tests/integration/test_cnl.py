import pytest
from werkzeug.middleware.proxy_fix import ProxyFix


class TestClickNLoad:
    def test_cnl_disabled_by_default(self, client):
        response = client.get("http://localhost:9666/jdcheck.js")

        assert response.status_code == 404

    def test_jdcheck_successful_when_cnl_activated(self, pyload_core, client):
        pyload_core.config.set_plugin("ClickNLoad", "enabled", True)

        response = client.get("http://localhost:9666/jdcheck.js")

        assert response.status_code == 200

    @pytest.mark.parametrize("http_host", ["localhost", "127.0.0.1", "[::1]"])
    def test_valid_hosts(self, pyload_core, client, http_host):
        pyload_core.config.set_plugin("ClickNLoad", "enabled", True)

        response = client.get(f"http://{http_host}:9666/jdcheck.js")

        assert response.status_code == 200

    @pytest.mark.parametrize("http_host", ["192.168.0.1", "0.0.0.0"])
    def test_invalid_host_headers(
        self, pyload_core, client, http_host
    ):
        pyload_core.config.set_plugin("ClickNLoad", "enabled", True)

        response = client.get(
            "http://localhost:9666/jdcheck.js",
            headers={"Host": f"{http_host}:9666"},
        )

        assert response.status_code == 403

    def test_remote_peer_cannot_spoof_local_forwarded_address(
        self, pyload_core, client
    ):
        pyload_core.config.set_plugin("ClickNLoad", "enabled", True)

        response = client.get(
            "http://localhost:9666/jdcheck.js",
            headers={"X-Forwarded-For": "127.0.0.1"},
            environ_base={"REMOTE_ADDR": "203.0.113.10"},
        )

        assert response.status_code == 403

    def test_local_check_rejects_remote_peer_even_with_proxy_fix(
        self, app, pyload_core, client, monkeypatch
    ):
        pyload_core.config.set_plugin("ClickNLoad", "enabled", True)
        wsgi_app = getattr(app, "wsgi_app")
        monkeypatch.setitem(app.__dict__, "wsgi_app", ProxyFix(wsgi_app, x_for=1))

        response = client.get(
            "http://localhost:9666/jdcheck.js",
            headers={"X-Forwarded-For": "127.0.0.1"},
            environ_base={"REMOTE_ADDR": "203.0.113.10"},
        )

        assert response.status_code == 403

    def test_remote_peer_cannot_use_local_clicknload_host(
        self, pyload_core, client
    ):
        pyload_core.config.set_plugin("ClickNLoad", "enabled", True)

        response = client.get(
            "http://localhost:9666/jdcheck.js",
            environ_base={"REMOTE_ADDR": "203.0.113.10"},
        )

        assert response.status_code == 403
