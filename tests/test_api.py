import time
import pytest


API_KEY_HEADER = "X-API-KEY"


class TestAuthorization:
    def test_error_when_missing_auth(self, client):
        response = client.get("/api/status_server")

        assert response.status_code == 401

        response = client.post("/api/restart")

        assert response.status_code == 401

    @pytest.mark.parametrize(
        "invalid_api_key",
        [
            None, "", "x", "pl_123456",
        ]
    )
    def test_error_when_invalid_auth(self, client, invalid_api_key):
        response = client.get("/api/status_server", headers={API_KEY_HEADER: invalid_api_key})

        assert response.status_code == 401

        response = client.post("/api/restart", headers={API_KEY_HEADER: invalid_api_key})

        assert response.status_code == 401

    def test_error_when_auth_expired(self, pyload_core, client):
        expired_api_key = pyload_core.api.generate_apikey("pyload", "pyload", expires=int(time.time() * 1000))["data"]["key"]

        response = client.get("/api/status_server", headers={API_KEY_HEADER: expired_api_key})

        assert response.status_code == 401

        response = client.post("/api/restart", headers={API_KEY_HEADER: expired_api_key})

        assert response.status_code == 401

    def test_success_with_valid_auth_without_expiry(self, api_key, client):
        response = client.get("/api/status_server", headers={API_KEY_HEADER: api_key})

        assert response.status_code == 200
        assert response.json["active"] == 0

        response = client.post("/api/restart", headers={API_KEY_HEADER: api_key})

        assert response.status_code == 200

    def test_success_with_valid_auth_with_expiry(self, pyload_core, client):
        expiry_date = int(time.time() * 1000) + 1000
        valid_api_key = pyload_core.api.generate_apikey("pyload", "pyload", expires=expiry_date)["data"]["key"]

        response = client.get("/api/status_server", headers={API_KEY_HEADER: valid_api_key})

        assert response.status_code == 200
        assert response.json["active"] == 0

        response = client.post("/api/restart", headers={API_KEY_HEADER: valid_api_key})

        assert response.status_code == 200


class TestPackages:
    @pytest.mark.parametrize(
        ("destination", "destination_id"),
        [
            ("collector", 0),
            ("queue", 1),
        ]
    )
    def test_add_and_remove_package(self, api_key, client, destination, destination_id):
        # Assert no packages in destination at the start
        response = client.get(f"api/get_{destination}", headers={API_KEY_HEADER: api_key})

        assert response.status_code == 200
        assert len(response.json) == 0

        # Add a dummy package to the destination
        response = client.post(
            "/api/add_package",
            json={
                "name": "test_package",
                "links": [
                    "https://localhost/non-existent-file.zip"
                ],
                "dest": destination_id
            },
            headers={API_KEY_HEADER: api_key}
        )

        assert response.status_code == 200
        package_id = response.text

        # Assert destination contains dummy package
        response = client.get(f"api/get_{destination}", headers={API_KEY_HEADER: api_key})

        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]["name"] == "test_package"
        assert response.json[0]["pid"] == int(package_id)

        # Delete package
        response = client.post(
            "/api/delete_packages",
            json={
                "package_ids": [package_id]
            },
            headers={API_KEY_HEADER: api_key}
        )

        assert response.status_code == 200

        # Assert destination is empty again
        response = client.get(f"api/get_{destination}", headers={API_KEY_HEADER: api_key})

        assert response.status_code == 200
        assert len(response.json) == 0

    def test_move_package(self, api_key, client):
        # Add a dummy package to the collector
        response = client.post(
            "/api/add_package",
            json={
                "name": "test_package",
                "links": [
                    "https://localhost/non-existent-file.zip"
                ],
                "dest": 0
            },
            headers={API_KEY_HEADER: api_key}
        )

        assert response.status_code == 200
        package_id = response.text

        # Move package to queue
        response = client.post(
            "/api/move_package",
            query_string={"destination": 1, "package_id": package_id},
            headers={API_KEY_HEADER: api_key}
        )

        assert response.status_code == 200

        # Assert package is now in queue and no longer in collector
        response = client.get("api/get_queue", headers={API_KEY_HEADER: api_key})

        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]["name"] == "test_package"
        assert response.json[0]["pid"] == int(package_id)

        response = client.get("api/get_collector", headers={API_KEY_HEADER: api_key})

        assert response.status_code == 200
        assert len(response.json) == 0

        # Delete package again
        response = client.post(
            "/api/delete_packages",
            json={
                "package_ids": [package_id]
            },
            headers={API_KEY_HEADER: api_key}
        )

        assert response.status_code == 200
