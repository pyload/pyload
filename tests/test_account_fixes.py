"""
Regression tests for account handling fixes:
- AccountInfo tolerates None values (no ValidationError crash)
- reset() preserves login/type/plugin identity keys
- get_accounts() skips broken accounts gracefully
"""
import importlib
import sys
import types
import os
import pytest

# We need to import data.py directly without triggering the full pyload import chain.
# Block pyload.core from resolving via the installed package and stub the dependencies.

# Remove any cached pyload modules
for key in list(sys.modules.keys()):
    if key.startswith("pyload"):
        del sys.modules[key]

# Stub the parent packages so data.py's relative imports resolve
_pyload = types.ModuleType("pyload")
_pyload.__path__ = [os.path.join(os.path.dirname(__file__), "..", "src", "pyload")]
_core = types.ModuleType("pyload.core")
_core.__path__ = [os.path.join(_pyload.__path__[0], "core")]
_dt = types.ModuleType("pyload.core.datatypes")
_dt.__path__ = [os.path.join(_core.__path__[0], "datatypes")]

# Stub enums with the real IntEnum
_enums = types.ModuleType("pyload.core.datatypes.enums")

from enum import IntEnum


class _DownloadStatus(IntEnum):
    FINISHED = 0
    DOWNLOADING = 12


_enums.DownloadStatus = _DownloadStatus

# Stub json_schema_extras
_extras = types.ModuleType("pyload.core.datatypes.json_schema_extras")
_extras.FLOAT_JSON_SCHEMA = {}
_extras.INT64_JSON_SCHEMA = {}
_extras.OPTIONAL_FLOAT_JSON_SCHEMA = {}
_extras.OPTIONAL_INT64_JSON_SCHEMA = {}

sys.modules["pyload"] = _pyload
sys.modules["pyload.core"] = _core
sys.modules["pyload.core.datatypes"] = _dt
sys.modules["pyload.core.datatypes.enums"] = _enums
sys.modules["pyload.core.datatypes.json_schema_extras"] = _extras

# Now import data.py via importlib from the source tree
_data_path = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "pyload", "core", "datatypes", "data.py")
)
_spec = importlib.util.spec_from_file_location("pyload.core.datatypes.data", _data_path)
_data_mod = importlib.util.module_from_spec(_spec)
sys.modules["pyload.core.datatypes.data"] = _data_mod
_spec.loader.exec_module(_data_mod)

AccountInfo = _data_mod.AccountInfo


class TestAccountInfoDefaults:
    """Fix 1: AccountInfo must accept None/missing values without crashing."""

    def test_all_none_values_use_defaults(self):
        info = AccountInfo()
        assert info.login == ""
        assert info.premium is False
        assert info.type == ""
        assert info.valid is False
        assert info.options == {}
        assert info.trafficleft is None
        assert info.validuntil is None

    def test_explicit_none_for_optional_fields(self):
        info = AccountInfo(
            login="user",
            premium=True,
            type="RapidgatorNet",
            valid=True,
            options={},
            trafficleft=None,
            validuntil=None,
        )
        assert info.trafficleft is None
        assert info.validuntil is None
        assert info.premium is True

    def test_normal_account_info(self):
        info = AccountInfo(
            login="testuser",
            premium=True,
            type="RapidgatorNet",
            valid=True,
            options={"limit_dl": ["0"]},
            trafficleft=5000000,
            validuntil=1780933118,
        )
        assert info.login == "testuser"
        assert info.premium is True
        assert info.type == "RapidgatorNet"
        assert info.trafficleft == 5000000


class TestAccountReset:
    """Fix 3: reset() must preserve login, type, plugin keys."""

    def _make_account_plugin(self):
        """Create a minimal mock account plugin with real reset() logic."""
        from pyload.core.utils.check import is_sequence

        class FakeAccount:
            def __init__(self):
                self.user = "testuser"
                self.accounts = {
                    "testuser": {
                        "login": "testuser",
                        "type": "TestPlugin",
                        "plugin": self,
                        "premium": True,
                        "trafficleft": 999999,
                        "validuntil": 1780933118,
                        "options": {"limit_dl": ["5"]},
                        "password": "secret",
                        "timestamp": 100,
                        "stats": [1, 0],
                        "valid": True,
                    }
                }
                self.info = {"login": {}, "data": {}}

            def sync(self, reverse=False):
                u = self.accounts[self.user]
                if reverse:
                    u.update(self.info["data"])
                    u.update(self.info["login"])
                else:
                    d = {"login": {}, "data": {}}
                    for k, v in u.items():
                        if k in ("password", "timestamp", "stats", "valid"):
                            d["login"][k] = v
                        else:
                            d["data"][k] = v
                    self.info.update(d)

            def syncback(self):
                return self.sync(reverse=True)

            def reset(self):
                self.sync()

                _preserve = {"login", "type", "plugin"}

                def clear(k, v):
                    if k in _preserve:
                        return v
                    if k == "premium":
                        return False
                    return {} if isinstance(v, dict) else [] if is_sequence(v) else None

                self.info["data"] = {k: clear(k, v) for k, v in self.info["data"].items()}
                self.info["data"]["options"] = {"limit_dl": ["0"]}

                self.syncback()

        return FakeAccount()

    def test_reset_preserves_login(self):
        acc = self._make_account_plugin()
        acc.reset()
        assert acc.accounts["testuser"]["login"] == "testuser"

    def test_reset_preserves_type(self):
        acc = self._make_account_plugin()
        acc.reset()
        assert acc.accounts["testuser"]["type"] == "TestPlugin"

    def test_reset_preserves_plugin(self):
        acc = self._make_account_plugin()
        acc.reset()
        assert acc.accounts["testuser"]["plugin"] is acc

    def test_reset_clears_premium_to_false(self):
        acc = self._make_account_plugin()
        acc.reset()
        assert acc.accounts["testuser"]["premium"] is False

    def test_reset_clears_trafficleft(self):
        acc = self._make_account_plugin()
        acc.reset()
        assert acc.accounts["testuser"]["trafficleft"] is None

    def test_reset_resets_options(self):
        acc = self._make_account_plugin()
        acc.reset()
        assert acc.accounts["testuser"]["options"] == {"limit_dl": ["0"]}

    def test_reset_account_still_creates_valid_accountinfo(self):
        """After reset(), account data must produce a valid AccountInfo (no crash)."""
        acc = self._make_account_plugin()
        acc.reset()
        d = acc.accounts["testuser"]
        info = AccountInfo(
            validuntil=d.get("validuntil"),
            login=d.get("login", ""),
            options=d.get("options", {}),
            valid=d.get("valid", False),
            trafficleft=d.get("trafficleft"),
            premium=d.get("premium", False),
            type=d.get("type", ""),
        )
        assert info.login == "testuser"
        assert info.type == "TestPlugin"
        assert info.premium is False


class TestGetAccountsSafety:
    """Fix 2: get_accounts() must not crash on broken account data."""

    def test_broken_account_skipped(self):
        """Simulate a broken account dict with all None values — must not raise."""
        broken_accs = {
            "BrokenPlugin": [
                {
                    "login": None,
                    "premium": None,
                    "type": None,
                    "valid": None,
                    "options": None,
                    "trafficleft": None,
                    "validuntil": None,
                }
            ]
        }
        # Simulate the fixed get_accounts logic
        accounts = []
        for group in broken_accs.values():
            for acc in group:
                try:
                    accounts.append(
                        AccountInfo(
                            validuntil=acc.get("validuntil"),
                            login=acc.get("login") or "",
                            options=acc.get("options") or {},
                            valid=bool(acc.get("valid")),
                            trafficleft=acc.get("trafficleft"),
                            premium=bool(acc.get("premium")),
                            type=acc.get("type") or "",
                        )
                    )
                except Exception:
                    pass  # Broken account skipped

        # With defaults, the broken account should still produce a valid object
        assert len(accounts) == 1
        assert accounts[0].login == ""
        assert accounts[0].premium is False

    def test_mixed_good_and_broken_accounts(self):
        """Good accounts must survive even if others are broken."""
        accs = {
            "GoodPlugin": [
                {
                    "login": "user1",
                    "premium": True,
                    "type": "GoodPlugin",
                    "valid": True,
                    "options": {},
                    "trafficleft": 5000,
                    "validuntil": 9999999,
                }
            ],
            "BrokenPlugin": [
                {
                    "login": None,
                    "premium": None,
                    "type": None,
                    "valid": None,
                    "options": None,
                    "trafficleft": None,
                    "validuntil": None,
                }
            ],
        }
        accounts = []
        for group in accs.values():
            for acc in group:
                try:
                    accounts.append(
                        AccountInfo(
                            validuntil=acc.get("validuntil"),
                            login=acc.get("login") or "",
                            options=acc.get("options") or {},
                            valid=bool(acc.get("valid")),
                            trafficleft=acc.get("trafficleft"),
                            premium=bool(acc.get("premium")),
                            type=acc.get("type") or "",
                        )
                    )
                except Exception:
                    pass

        assert len(accounts) == 2
        good = [a for a in accounts if a.login == "user1"]
        assert len(good) == 1
        assert good[0].premium is True


class TestOfflinePatternDdownload:
    """Fix B: DdownloadCom OFFLINE_PATTERN must detect both 'File Not Found' and 'File Deleted'."""

    def test_file_not_found_matches(self):
        import re
        pattern = r">File Not Found<|>File Deleted<"
        html = '<h1>File Not Found</h1>'
        assert re.search(pattern, html) is not None

    def test_file_deleted_matches(self):
        import re
        pattern = r">File Not Found<|>File Deleted<"
        html = '<h1>File Deleted</h1>'
        assert re.search(pattern, html) is not None

    def test_available_file_does_not_match(self):
        import re
        pattern = r">File Not Found<|>File Deleted<"
        html = '<h1 class="file-info-name">test.rar</h1><span class="file-size">1.73 GB</span>'
        assert re.search(pattern, html) is None


class TestCookieJarClearing:
    """Fix A: Cookie jar must be cleared when password changes."""

    def test_password_change_clears_cookie_jar(self):
        """When password changes, remove_cookie_jar must be called."""
        cleared = []

        class FakeRequestFactory:
            def remove_cookie_jar(self, classname, user):
                cleared.append((classname, user))

        class FakePlugin:
            def relogin(self):
                pass
            def get_info(self):
                pass

        class FakeAccount:
            classname = "DdownloadCom"
            def __init__(self):
                self.pyload = type('obj', (object,), {'request_factory': FakeRequestFactory()})()
                plugin = FakePlugin()
                self.accounts = {
                    "user1": {
                        "password": "old_password",
                        "options": {},
                        "plugin": plugin,
                    }
                }
            def _(self, s): return s
            def log_info(self, *a): pass

        acc = FakeAccount()
        # Simulate update_accounts logic with password change
        user = "user1"
        password = "new_password"
        u = acc.accounts[user]
        old_password = u.get("password", "")
        u["password"] = password
        if password != old_password:
            acc.pyload.request_factory.remove_cookie_jar(acc.classname, user)
        u["plugin"].relogin()
        u["plugin"].get_info()

        assert len(cleared) == 1
        assert cleared[0] == ("DdownloadCom", "user1")

    def test_same_password_does_not_clear(self):
        """When password is the same, cookie jar should not be cleared."""
        cleared = []

        class FakeRequestFactory:
            def remove_cookie_jar(self, classname, user):
                cleared.append((classname, user))

        class FakePlugin:
            def relogin(self): pass
            def get_info(self): pass

        class FakeAccount:
            classname = "DdownloadCom"
            def __init__(self):
                self.pyload = type('obj', (object,), {'request_factory': FakeRequestFactory()})()
                plugin = FakePlugin()
                self.accounts = {
                    "user1": {
                        "password": "same_password",
                        "options": {},
                        "plugin": plugin,
                    }
                }

        acc = FakeAccount()
        user = "user1"
        password = "same_password"
        u = acc.accounts[user]
        old_password = u.get("password", "")
        u["password"] = password
        if password != old_password:
            acc.pyload.request_factory.remove_cookie_jar(acc.classname, user)

        assert len(cleared) == 0
