"""Regression tests for invalidating Flask sessions after REST account changes."""

import time

API_KEY_HEADER = "X-API-KEY"


def _create_logged_in_user(app, client, api_key, username, password):
    response = client.post(
        "/api/add_user",
        query_string={"user": username, "newpw": password},
        headers={API_KEY_HEADER: api_key},
    )
    assert response.status_code == 200

    user_client = app.test_client()
    response = user_client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert response.status_code == 200
    return user_client


def _remove_user(client, api_key, username):
    response = client.post(
        "/api/remove_user",
        query_string={"user": username},
        headers={API_KEY_HEADER: api_key},
    )
    assert response.status_code == 200


def test_set_user_permission_invalidates_logged_in_user(app, api_key, client):
    app.config.update({"WTF_CSRF_ENABLED": False})
    username = f"session_role_test_{int(time.time() * 1000)}"
    password = "initial_password"
    user_client = _create_logged_in_user(
        app, client, api_key, username, password
    )

    try:
        response = user_client.get("/api/get_userdir")
        assert response.status_code == 200

        response = client.post(
            "/api/set_user_permission",
            query_string={"user": username, "permission": 0, "role": 1},
            headers={API_KEY_HEADER: api_key},
        )
        assert response.status_code == 200

        response = user_client.get("/api/get_userdir")
        assert response.status_code == 401
    finally:
        _remove_user(client, api_key, username)


def test_set_user_permission_invalidates_the_current_session(
    app, api_key, client
):
    app.config.update({"WTF_CSRF_ENABLED": False})
    username = f"session_self_role_test_{int(time.time() * 1000)}"
    user_client = _create_logged_in_user(
        app, client, api_key, username, "initial_password"
    )

    try:
        response = user_client.post(
            "/api/set_user_permission",
            query_string={"user": username, "permission": 0, "role": 1},
            headers={API_KEY_HEADER: api_key},
        )
        assert response.status_code == 200

        response = user_client.get("/api/get_userdir")
        assert response.status_code == 401
    finally:
        _remove_user(client, api_key, username)


def test_change_password_invalidates_logged_in_user(app, api_key, client):
    app.config.update({"WTF_CSRF_ENABLED": False})
    username = f"session_password_test_{int(time.time() * 1000)}"
    old_password = "initial_password"
    user_client = _create_logged_in_user(
        app, client, api_key, username, old_password
    )

    try:
        response = user_client.get("/api/get_userdir")
        assert response.status_code == 200

        response = client.post(
            "/api/change_password",
            query_string={
                "user": username,
                "oldpw": old_password,
                "newpw": "updated_password",
            },
            headers={API_KEY_HEADER: api_key},
        )
        assert response.status_code == 200
        assert response.json is True

        response = user_client.get("/api/get_userdir")
        assert response.status_code == 401
    finally:
        _remove_user(client, api_key, username)
