"""Tests for cache synchronization with API-key revocation."""

from threading import Event, Thread

from pyload.core.api import Api


def test_delete_apikey_waits_for_inflight_cache_miss():
    api_key = "pl_11" + "a" * 43
    core = type("Core", (), {})()
    core._ = lambda value: value
    core.db = type("Database", (), {})()
    api = Api(core)

    validation_started = Event()
    finish_validation = Event()
    delete_reached_database = Event()
    key_data = {
        "id": 1,
        "user_id": 7,
        "expires_at": 0,
        "name": "test key",
        "last_used": 0,
    }

    def check_key(_key_id, _token):
        validation_started.set()
        assert finish_validation.wait(timeout=2)
        return key_data

    def delete_key(_user_id, _key_id):
        delete_reached_database.set()
        return True

    core.db.check_apikey = check_key
    core.db.update_apikey_last_used = lambda _key_id: None
    core.db.get_user_id = lambda _username: 7
    core.db.delete_user_apikey = delete_key

    validation_result = []
    validation = Thread(
        target=lambda: validation_result.append(api.check_apikey(api_key))
    )
    deletion = Thread(target=lambda: api.delete_apikey("test-user", 1))

    validation.start()
    assert validation_started.wait(timeout=2)
    deletion.start()

    assert not delete_reached_database.wait(timeout=0.05)
    finish_validation.set()
    validation.join(timeout=2)
    deletion.join(timeout=2)

    assert not validation.is_alive()
    assert not deletion.is_alive()
    assert validation_result[0]["success"] is True
    assert delete_reached_database.is_set()
    assert api._apikey_cache == {}


def test_remove_user_clears_cached_api_keys():
    core = type("Core", (), {})()
    core._ = lambda value: value
    core.db = type("Database", (), {})()
    api = Api(core)
    api._apikey_cache["cached-key"] = (
        0,
        {"id": 1, "user_id": 7},
    )
    core.db.get_user_id = lambda _username: 7
    core.db.remove_user = lambda _username: True

    assert api.remove_user("test-user") is True
    assert api._apikey_cache == {}
