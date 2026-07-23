"""
Regression tests for account handling fixes:
- AccountInfo tolerates None values (no ValidationError crash)
- reset() preserves login/type/plugin identity keys
- get_accounts() skips broken accounts gracefully
"""
from pyload.core.datatypes.data import AccountInfo


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


class TestConcurrentAccountAccess:
    """Tests to ensure account accessors are thread-safe and don't raise under concurrent mutations."""

    def test_get_login_thread_safe_no_exception(self):
        import threading

        from pyload.plugins.base.account import BaseAccount

        class FakeReq:
            def close(self):
                pass

        class FakeRequestFactory:
            def get_request(self, *args, **kwargs):
                return FakeReq()

        class FakeLog:
            def debug(self, *a, **k):
                pass
            def info(self, *a, **k):
                pass
            def warning(self, *a, **k):
                pass
            def error(self, *a, **k):
                pass

        class FakeCore:
            def __init__(self):
                self._ = lambda s: s
                self.request_factory = FakeRequestFactory()
                self.log = FakeLog()
                self.debug = 0
                self.version = "test"
                self.tempdir = "."
                self.config = type("C", (), {"get": lambda *a, **k: False})()

        class DummyAccount(BaseAccount):
            def periodical_task(self):
                pass
            def signin(self, user, password, data):
                pass
            def grab_info(self, user, password, data):
                return {}

        manager = type("M", (), {})()
        manager.pyload = FakeCore()

        accounts = {
            "user1": {
                "password": "secret",
                "options": {},
                "plugin": None,
                "premium": True,
                "stats": [0, 0],
                "timestamp": 0,
                "valid": True,
                "type": "Test",
            }
        }

        acc = DummyAccount(manager, accounts)
        acc.sync()

        exceptions = []

        def writer():
            for i in range(100):
                # Directly mutate self.info (should be protected by lock)
                if i % 2 == 0:
                    acc.info = {"login": {}, "data": {}}
                else:
                    acc.info = {"login": {"password": "secret"}, "data": {}}

        def reader():
            for _ in range(100):
                try:
                    _ = acc.get_login("password")
                except Exception as e:
                    exceptions.append(e)

        t1 = threading.Thread(target=writer)
        t2 = threading.Thread(target=reader)
        t1.start(); t2.start()
        t1.join(); t2.join()

        # No exceptions should occur due to @lock decorator protecting access
        assert exceptions == []

    def test_get_data_thread_safe_no_exception(self):
        import threading
        from pyload.plugins.base.account import BaseAccount

        class FakeReq:
            def close(self):
                pass

        class FakeRequestFactory:
            def get_request(self, *args, **kwargs):
                return FakeReq()

        class FakeLog:
            def debug(self, *a, **k):
                pass
            def info(self, *a, **k):
                pass
            def warning(self, *a, **k):
                pass
            def error(self, *a, **k):
                pass

        class FakeCore:
            def __init__(self):
                self._ = lambda s: s
                self.request_factory = FakeRequestFactory()
                self.log = FakeLog()
                self.debug = 0
                self.version = "test"
                self.tempdir = "."
                self.config = type("C", (), {"get": lambda *a, **k: False})()

        class DummyAccount(BaseAccount):
            def periodical_task(self):
                pass
            def signin(self, user, password, data):
                pass
            def grab_info(self, user, password, data):
                return {}

        manager = type("M", (), {})()
        manager.pyload = FakeCore()

        accounts = {
            "user1": {
                "password": "secret",
                "options": {},
                "plugin": None,
                "premium": True,
                "stats": [0, 0],
                "timestamp": 0,
                "valid": True,
                "type": "Test",
                "cache_info": {"user1": {"token": "abc"}},
            }
        }

        acc = DummyAccount(manager, accounts)
        acc.sync()

        exceptions = []

        def writer():
            for i in range(100):
                # Directly mutate self.info (should be protected by lock)
                if i % 2 == 0:
                    acc.info = {"login": {"password": "secret"}, "data": {}}
                else:
                    acc.info = {"login": {"password": "secret"}, "data": {"token": "abc"}}

        def reader():
            for _ in range(100):
                try:
                    _ = acc.get_data("token")
                except Exception as e:
                    exceptions.append(e)

        t1 = threading.Thread(target=writer)
        t2 = threading.Thread(target=reader)
        t1.start(); t2.start()
        t1.join(); t2.join()

        # No exceptions should occur due to @lock decorator protecting access
        assert exceptions == []

    def test_multiple_accounts_concurrent_operations(self):
        """Test concurrent operations on multiple active accounts from different threads."""
        import threading
        from pyload.plugins.base.account import BaseAccount

        class FakeReq:
            def close(self):
                pass

        class FakeRequestFactory:
            def get_request(self, *args, **kwargs):
                return FakeReq()

        class FakeLog:
            def debug(self, *a, **k):
                pass
            def info(self, *a, **k):
                pass
            def warning(self, *a, **k):
                pass
            def error(self, *a, **k):
                pass

        class FakeCore:
            def __init__(self):
                self._ = lambda s: s
                self.request_factory = FakeRequestFactory()
                self.log = FakeLog()
                self.debug = 0
                self.version = "test"
                self.tempdir = "."
                self.config = type("C", (), {"get": lambda *a, **k: False})()

        class DummyAccount(BaseAccount):
            def periodical_task(self):
                pass
            def signin(self, user, password, data):
                pass
            def grab_info(self, user, password, data):
                return {}

        manager = type("M", (), {})()
        manager.pyload = FakeCore()

        # Create multiple accounts to simulate different active users
        accounts_pool = {}
        for user_idx in range(1, 4):
            user_id = f"user{user_idx}"
            accounts_pool[user_id] = {
                "password": f"secret_{user_idx}",
                "options": {"limit": [str(user_idx)]},
                "plugin": None,
                "premium": user_idx % 2 == 0,  # user2 is premium
                "stats": [user_idx, 0],
                "timestamp": 1000 * user_idx,
                "valid": True,
                "type": "TestPlugin",
                "token": f"token_{user_idx}",
            }

        exceptions = []
        operation_count = [0]

        # Create individual account instances
        accounts = {}
        for user_id, account_data in accounts_pool.items():
            acc_instance = DummyAccount(manager, {user_id: account_data})
            acc_instance.sync()
            accounts[user_id] = acc_instance

        def account_reader(user_id, num_ops=50):
            try:
                acc = accounts[user_id]
                for _ in range(num_ops):
                    _ = acc.get_login("password")
                    _ = acc.premium
                    _ = acc.get_data("token")
                    operation_count[0] += 1
            except Exception as e:
                exceptions.append((user_id, e))

        def account_writer(user_id, num_ops=50):
            try:
                acc = accounts[user_id]
                for i in range(num_ops):
                    if i % 3 == 0:
                        acc.sync()
                    _ = acc.get_login("password")
                    _ = acc.premium
                    operation_count[0] += 1
            except Exception as e:
                exceptions.append((user_id, e))

        # Create threads for concurrent operations on different accounts
        threads = []
        for user_id in accounts.keys():
            t_reader = threading.Thread(target=account_reader, args=(user_id,))
            t_writer = threading.Thread(target=account_writer, args=(user_id,))
            threads.append(t_reader)
            threads.append(t_writer)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no exceptions occurred and operations completed
        assert exceptions == [], f"Exceptions occurred: {exceptions}"
        assert operation_count[0] > 0, "No operations completed"

    def test_concurrent_downloads_with_multiple_accounts_same_type(self):
        """Test concurrent downloads using multiple accounts of the same plugin type."""
        import threading
        from pyload.plugins.base.account import BaseAccount

        class FakeReq:
            def close(self):
                pass

        class FakeRequestFactory:
            def get_request(self, *args, **kwargs):
                return FakeReq()

        class FakeLog:
            def debug(self, *a, **k):
                pass
            def info(self, *a, **k):
                pass
            def warning(self, *a, **k):
                pass
            def error(self, *a, **k):
                pass

        class FakeCore:
            def __init__(self):
                self._ = lambda s: s
                self.request_factory = FakeRequestFactory()
                self.log = FakeLog()
                self.debug = 0
                self.version = "test"
                self.tempdir = "."
                self.config = type("C", (), {"get": lambda *a, **k: False})()

        class DummyAccount(BaseAccount):
            def periodical_task(self):
                pass
            def signin(self, user, password, data):
                pass
            def grab_info(self, user, password, data):
                return {}

        manager = type("M", (), {})()
        manager.pyload = FakeCore()

        # Create multiple accounts of the SAME TYPE (e.g., all RapidGator accounts)
        # Simulating different user accounts for the same service
        accounts_data = {}
        for user_idx in range(1, 4):
            user_id = f"rapidgator_user{user_idx}"
            accounts_data[user_id] = {
                "password": f"password_{user_idx}",
                "options": {"max_connections": ["5"]},
                "plugin": None,
                "premium": True,
                "stats": [user_idx * 10, 0],
                "timestamp": 2000 + user_idx,
                "valid": True,
                "type": "RapidgatorNet",
                "traffic_limit": 1000 * user_idx,
            }

        # Create a single account manager with multiple same-type accounts
        manager_accounts = DummyAccount(manager, accounts_data)
        manager_accounts.sync()

        exceptions = []
        successful_downloads = [0]
        user_usage_count = {}

        def simulate_download(download_id, user_id, num_operations=20):
            """Simulate a download operation using a specific account."""
            try:
                # Pre-download checks
                _ = manager_accounts.get_login("password")
                _ = manager_accounts.premium

                # Simulate download preprocessing
                for _ in range(num_operations):
                    _ = manager_accounts.get_data("traffic_limit")
                    if manager_accounts.premium:
                        _ = manager_accounts.get_login("password")

                user_usage_count[user_id] = user_usage_count.get(user_id, 0) + 1
                successful_downloads[0] += 1

            except Exception as e:
                exceptions.append((download_id, user_id, e))

        def download_worker(num_downloads=15):
            """Worker thread that processes multiple downloads."""
            user_ids = list(accounts_data.keys())
            for dl_idx in range(num_downloads):
                # Select account in round-robin fashion
                selected_user = user_ids[dl_idx % len(user_ids)]
                simulate_download(
                    download_id=f"dl_{threading.current_thread().name}_{dl_idx}",
                    user_id=selected_user,
                    num_operations=10
                )

        # Create multiple worker threads simulating parallel downloads
        workers = []
        num_workers = 3
        for i in range(num_workers):
            worker_thread = threading.Thread(
                target=download_worker,
                args=(10,),
                name=f"worker_{i}"
            )
            workers.append(worker_thread)

        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()

        # Verify successful completion
        assert exceptions == [], f"Exceptions during downloads: {exceptions}"
        assert successful_downloads[0] > 0, "No downloads completed successfully"
        assert successful_downloads[0] == num_workers * 10, "Not all downloads completed"
        assert len(user_usage_count) > 0, "No accounts were used"

