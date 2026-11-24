import socket
from unittest.mock import MagicMock, patch

import pytest

from pyload import g
from pyload.plugins.addons.ClickNLoad import ClickNLoad


@pytest.fixture
def cnl_addon():
    obj = ClickNLoad.__new__(ClickNLoad)
    obj._ = lambda s: s
    obj.pyload = MagicMock()
    obj.pyload.exiting = False
    obj.pyload.config.get.side_effect = lambda cat, key: {
        ("webui", "enabled"): True,
        ("webui", "host"): "127.0.0.1",
        ("webui", "port"): 8000,
    }.get((cat, key), None)
    obj.pyload.webserver.use_ssl = False

    obj.config = MagicMock()
    obj.config.get.side_effect = lambda key: {
        "extern": False,
        "port": 9666,
        "dest": "collector",
        "hosts_filter": "",
    }.get(key, None)

    for name in ("log_error", "log_info", "log_debug", "log_warning"):
        setattr(obj, name, MagicMock())

    obj.proxy = MagicMock()
    obj.init()
    return obj


def test_init_sets_initial_state(cnl_addon):
    assert cnl_addon.cnl_ip == "127.0.0.1"
    assert cnl_addon.cnl_port == 9666
    assert cnl_addon.server_running is False
    assert cnl_addon.do_exit is False
    assert not cnl_addon.backend_found.is_set()
    assert cnl_addon.web_addr is None
    assert cnl_addon.web_af is None


def test_find_backend_success(cnl_addon):
    mock_socket = MagicMock()
    with patch("socket.socket", return_value=mock_socket):
        result = cnl_addon._find_backend()

    assert result is True
    assert cnl_addon.backend_found.is_set()
    assert cnl_addon.web_addr == ("127.0.0.1", 8000)
    assert g.get("web_addr") == "127.0.0.1"
    mock_socket.connect.assert_called_once()
    mock_socket.close.assert_called_once()


def test_find_backend_failure(cnl_addon):
    mock_socket = MagicMock()
    mock_socket.connect.side_effect = socket.error("Connection refused")
    with patch("socket.socket", return_value=mock_socket):
        result = cnl_addon._find_backend()

    assert result is False
    assert not cnl_addon.backend_found.is_set()
    mock_socket.close.assert_called_once()


def test_activate_retries_and_succeeds_when_backend_delayed(cnl_addon):
    # Simulate backend becoming available on 3rd attempt
    attempts = [False, False, True]

    def fake_find():
        res = attempts.pop(0)
        if res:
            cnl_addon.backend_found.set()
        return res

    cnl_addon._find_backend = fake_find

    # Run undecorated _activate
    ClickNLoad._activate.__wrapped__(cnl_addon, timeout=10, retry_interval=0.01)

    assert cnl_addon.proxy.called
    assert cnl_addon.backend_found.is_set()
    cnl_addon.log_error.assert_not_called()


def test_activate_stops_on_do_exit(cnl_addon):
    call_count = 0

    def fake_find():
        nonlocal call_count
        call_count += 1
        cnl_addon.do_exit = True
        return False

    cnl_addon._find_backend = fake_find

    ClickNLoad._activate.__wrapped__(cnl_addon, timeout=10, retry_interval=0.01)

    assert call_count == 1
    assert not cnl_addon.proxy.called
    cnl_addon.log_error.assert_not_called()


def test_activate_times_out_and_logs_error(cnl_addon):
    cnl_addon._find_backend = MagicMock(return_value=False)

    ClickNLoad._activate.__wrapped__(cnl_addon, timeout=0.05, retry_interval=0.01)

    assert not cnl_addon.proxy.called
    cnl_addon.log_error.assert_called_once()


def test_activate_skips_when_webui_disabled(cnl_addon):
    cnl_addon.pyload.config.get.side_effect = lambda cat, key: False if (cat, key) == ("webui", "enabled") else None
    cnl_addon._activate = MagicMock()

    cnl_addon.activate()

    cnl_addon._activate.assert_not_called()
    cnl_addon.log_warning.assert_called_once()
