import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pyload.plugins.addons.Solvecha import Solvecha


class FakeTask:
    def __init__(self, path):
        self.captcha_params = {"file": path}
        self.data = {}
        self.error = None
        self.result = "unset"

    def set_result(self, result):
        self.result = result


@pytest.fixture
def addon(tmp_path):
    obj = Solvecha.__new__(Solvecha)
    obj.config = MagicMock()
    obj.config.get.side_effect = lambda key, default=None: {"passkey": "k"}.get(key, default)
    obj._ = lambda s: s
    for name in ("log_error", "log_info", "log_debug"):
        setattr(obj, name, MagicMock())
    obj.POLL_INTERVAL = 0
    img = tmp_path / "c.png"
    img.write_bytes(b"img")
    return obj, FakeTask(str(img))


def run(obj, task, responses, timeout=60):
    calls = []

    def fake(method, post):
        calls.append((method, post))
        return responses.pop(0)

    obj.api_request = fake
    # run the undecorated function
    Solvecha._process_captcha.__wrapped__(obj, task, timeout)
    return calls


def test_solution_returned_by_create_task(addon):
    obj, task = addon
    calls = run(obj, task, [
        {"errorId": 0, "taskId": "1", "status": "ready", "solution": {"text": "abc"}}
    ])
    assert task.result == "abc"
    assert [c[0] for c in calls] == ["createTask"]
    assert calls[0][1]["task"]["type"] == "ImageToTextTask"
    assert calls[0][1]["task"]["body"] == "aW1n"
    assert calls[0][1]["clientKey"] == "k"


def test_polls_until_ready(addon):
    obj, task = addon
    calls = run(obj, task, [
        {"errorId": 0, "taskId": "1", "status": "processing"},
        {"errorId": 0, "status": "processing"},
        {"errorId": 0, "status": "ready", "solution": {"text": "xyz"}},
    ])
    assert task.result == "xyz"
    assert [c[0] for c in calls] == ["createTask", "getTaskResult", "getTaskResult"]


def test_error_on_create_task(addon):
    obj, task = addon
    run(obj, task, [
        {"errorId": 1, "errorCode": "ERROR_KEY_DENIED_ACCESS", "errorDescription": "denied"}
    ])
    assert task.error == "denied"
    assert task.result == "unset"


def test_error_while_polling_sets_empty_result(addon):
    obj, task = addon
    run(obj, task, [
        {"errorId": 0, "taskId": "1", "status": "processing"},
        {"errorId": 2, "errorDescription": "boom"},
    ])
    assert task.error == "boom"
    assert task.result is None
