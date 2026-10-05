"""Unit tests for user-session invalidation in core API operations."""

from unittest.mock import MagicMock

import pytest

from pyload.core.api import Api


@pytest.fixture
def api_and_core():
    core = MagicMock()
    api = Api(core)
    core.api = api
    return api, core


def test_permission_update_invalidates_sessions_when_values_change(api_and_core):
    api, core = api_and_core
    invalidate = MagicMock()
    api.set_session_invalidator(invalidate)
    core.db.set_user_permission.return_value = True

    api.set_user_permission("test-user", 0, 1)

    core.db.set_user_permission.assert_called_once_with("test-user", 0, 1)
    invalidate.assert_called_once_with("test-user")


def test_permission_update_does_not_invalidate_unchanged_values(api_and_core):
    api, core = api_and_core
    invalidate = MagicMock()
    api.set_session_invalidator(invalidate)
    core.db.set_user_permission.return_value = False

    api.set_user_permission("test-user", 4, 0)

    core.db.set_user_permission.assert_called_once_with("test-user", 4, 0)
    invalidate.assert_not_called()


def test_permission_update_surfaces_invalidation_failure(api_and_core):
    api, core = api_and_core
    api.set_session_invalidator(
        MagicMock(side_effect=OSError("session store unavailable"))
    )
    core.db.set_user_permission.return_value = True

    with pytest.raises(OSError, match="session store unavailable"):
        api.set_user_permission("test-user", 0, 1)


def test_remove_user_invalidates_sessions_after_successful_delete(api_and_core):
    api, core = api_and_core
    invalidate = MagicMock()
    api.set_session_invalidator(invalidate)
    core.db.get_user_id.return_value = 42
    core.db.remove_user.return_value = True

    result = api.remove_user("test-user")

    assert result is True
    invalidate.assert_called_once_with("test-user")


@pytest.mark.parametrize(("changed", "should_invalidate"), [(True, True), (False, False)])
def test_password_change_invalidates_only_after_success(
    api_and_core, changed, should_invalidate
):
    api, core = api_and_core
    invalidate = MagicMock()
    api.set_session_invalidator(invalidate)
    core.db.change_password.return_value = changed

    result = api.change_password("test-user", "old", "new")

    assert result is changed
    if should_invalidate:
        invalidate.assert_called_once_with("test-user")
    else:
        invalidate.assert_not_called()


def test_session_invalidation_failure_is_propagated(api_and_core):
    api, core = api_and_core
    api.set_session_invalidator(
        MagicMock(side_effect=OSError("session store unavailable"))
    )
    core.db.change_password.return_value = True

    with pytest.raises(OSError, match="session store unavailable"):
        api.change_password("test-user", "old", "new")
