"""
Integration tests verifying protection against configuration injection (CRLF).
"""
import os
import pytest

from pyload.core.api import Perms

API_KEY_HEADER = "X-API-KEY"


class TestConfigInjectionSecurity:
    @pytest.fixture(autouse=True)
    def setup_user(self, pyload_core, api_key, client):
        client.application.config.update({"WTF_CSRF_ENABLED": False})

        # Create user with SETTINGS permission (Perms.SETTINGS = 128)
        self.username = "settings_attacker"
        self.password = "AttackerPassword123"

        client.post(
            "/api/add_user",
            query_string={
                "user": self.username,
                "newpw": self.password,
                "role": 1,
                "perms": int(Perms.SETTINGS)
            },
            headers={API_KEY_HEADER: api_key}
        )

        # Log in via session
        client.post(
            "/login",
            data={"username": self.username, "password": self.password},
            follow_redirects=True
        )

        yield

        # Cleanup user
        client.post(
            "/api/remove_user",
            query_string={"user": self.username},
            headers={API_KEY_HEADER: api_key}
        )

    def test_crlf_injection_payload_rejected_in_save_config(self, pyload_core, client):
        """
        Verify that newline injection through webui|theme is rejected and
        does not corrupt pyload.cfg or inject sections.
        """
        # Baseline settings
        orig_storage_folder = pyload_core.config.get("general", "storage_folder")
        orig_theme = pyload_core.config.get("webui", "theme")

        # The attack payload from the vulnerability report
        poc_payload = {
            "category": "core",
            "config": {
                "webui|theme": "modern\ngeneral - \"General\":\n\tfolder storage_folder : \"Injected\" = /tmp/evil\nreconnect - \"Reconnection\":\n\tstr script : \"Injected\" = /tmp/evil.sh\nwebui - \"Web Interface\":\n"
            }
        }

        # Send payload as the attacker
        resp = client.post(
            "/json/save_config",
            json=poc_payload
        )
        assert resp.status_code == 200

        # Verify running config values are NOT modified
        assert pyload_core.config.get("general", "storage_folder") == orig_storage_folder
        assert pyload_core.config.get("webui", "theme") == orig_theme
        assert pyload_core.config.get("reconnect", "script") != "/tmp/evil.sh"

        # Verify pyload.cfg file on disk does NOT contain injected sections or values
        cfg_path = pyload_core.config.configpath
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg_content = f.read()

        assert "/tmp/evil" not in cfg_content
        assert "/tmp/evil.sh" not in cfg_content

    def test_crlf_injection_rejected_for_str_options(self, pyload_core, client):
        """
        Verify that newlines are rejected in plain string options.
        """
        orig_user = pyload_core.config.get("permission", "user")

        payload = {
            "category": "core",
            "config": {
                "permission|user": "valid_user\ngeneral - \"General\":\n\tfolder storage_folder = /tmp/evil\n"
            }
        }

        resp = client.post(
            "/json/save_config",
            json=payload
        )
        assert resp.status_code == 200

        assert pyload_core.config.get("permission", "user") == orig_user

        cfg_path = pyload_core.config.configpath
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg_content = f.read()

        assert "/tmp/evil" not in cfg_content

    def test_legitimate_config_update_succeeds(self, pyload_core, client):
        """
        Verify that valid config updates with choice and string types succeed.
        """
        payload = {
            "category": "core",
            "config": {
                "webui|theme": "pyplex"
            }
        }

        resp = client.post(
            "/json/save_config",
            json=payload
        )
        assert resp.status_code == 200
        assert pyload_core.config.get("webui", "theme") == "pyplex"

        # Restore
        client.post(
            "/json/save_config",
            json={"category": "core", "config": {"webui|theme": "modern"}}
        )
        assert pyload_core.config.get("webui", "theme") == "modern"
