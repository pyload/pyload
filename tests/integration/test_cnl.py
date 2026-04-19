import pytest


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
    def test_invalid_host_headers(self, pyload_core, client, http_host):
        pyload_core.config.set_plugin("ClickNLoad", "enabled", True)

        response = client.get(f"http://localhost:9666/jdcheck.js", headers={"Host": f"{http_host}:9666"})

        assert response.status_code == 403
