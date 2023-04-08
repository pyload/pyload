# -*- coding: utf-8 -*-

import copy
import threading
import time
from datetime import timedelta

from pyload.core.network.exceptions import Skip
from pyload.core.utils import parse, seconds
from pyload.core.utils.struct.lock import lock

from ..helpers import Periodical, is_sequence
from .plugin import BasePlugin


class BaseAccount(BasePlugin):
    __name__ = "BaseAccount"
    __type__ = "account"
    __version__ = "0.90"
    __status__ = "stable"

    __description__ = """Base account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    #: Relogin account every 30 minutes, use -1 for never expire, you have to explicitly call relogin() when needed
    LOGIN_TIMEOUT = timedelta(minutes=30).total_seconds()
    TUNE_TIMEOUT = True  #: Automatically tune relogin interval

    def __init__(self, manager, accounts):
        self._init(manager.pyload)

        self.m = self.manager = manager
        self.lock = threading.RLock()

        self.accounts = accounts  # TODO: Recheck in 0.6.x
        self.user = None

        self.timeout = self.LOGIN_TIMEOUT

        #: Callback of periodical job task, used by AddonManager
        self.periodical = Periodical(self, self.periodical_task)
        self.cb = self.periodical.cb  # TODO: Recheck in 0.6.x

        self.init()

    def __bool__(self):
        return self.user is not None

    @property
    def logged(self):
        """
        Checks if user is still logged in.
        """
        if not self.user:
            return False

        self.sync()

        if (
            self.info["login"]["timestamp"] == 0
            or self.timeout != -1
            and self.info["login"]["timestamp"] + self.timeout < time.time()
        ):
            self.log_debug(f"Reached login timeout for user `{self.user}`")
            return False
        else:
            return True

    @property
    def premium(self):
        return bool(self.get_data("premium"))

    def _log(self, level, plugintype, pluginname, args, kwargs):
        log = getattr(self.pyload.log, level)

        #: Hide any user/password
        try:
            user = self.user
            hidden_user = "{:*<{}}".format(self.user[:3], 7)
            args = tuple(arg.replace(user, hidden_user) if isinstance(arg, str) else arg
                         for arg in args if arg)
        except (KeyError, TypeError):
            pass

        try:
            pw = self.info["login"]["password"]
            hidden_pw = "*" * 10
            args = tuple(arg.replace(pw, hidden_pw) if isinstance(arg, str) else arg
                         for arg in args if arg)
        except (KeyError, TypeError):
            pass

        log(
            "{plugintype} {pluginname}: {msg}".format(
                plugintype=plugintype.upper(),
                pluginname=pluginname,
                msg=" | ".join(["%s"] * len(args)),
            ),
            *args,
            **kwargs,
        )

    def setup(self):
        """
        Setup for environment and other things, called before logging (possibly more than
        one time)
        """
        pass

    def periodical_task(self):
        raise NotImplementedError

    def signin(self, user, password, data):
        """
        Login into account, the cookies will be saved so user can be recognized.
        """
        raise NotImplementedError

    def login(self):
        self.clean()
        self.sync()

        self.info["login"]["stats"][0] += 1
        if self.info["login"]["stats"][0] == 1:
            self.log_info(self._("Login user `{}`...").format(self.user))
        else:
            self.log_info(self._("Relogin user `{}`...").format(self.user))

        self.req = self.pyload.request_factory.get_request(self.classname, self.user)

        self.setup()

        timestamp = time.time()

        try:
            self.signin(self.user, self.info["login"]["password"], self.info["data"])

        except NotImplementedError:
            self.log_error(
                self._("Could not login user `{}`").format(self.user),
                self._("Plugin is missing a function")
            )

        except Skip as exc:
            self.log_warning(self._("Skipped login user `{}`").format(self.user), exc)
            self.info["login"]["valid"] = True

            new_timeout = timestamp - self.info["login"]["timestamp"]
            if self.TUNE_TIMEOUT and new_timeout > self.timeout:
                self.timeout = new_timeout

        except Exception as exc:
            self.log_error(self._("Could not login user `{}`").format(self.user), exc)
            self.info["login"]["valid"] = False

        else:
            self.info["login"]["valid"] = True

        finally:
            #: Set timestamp for login
            self.info["login"]["timestamp"] = timestamp

            self.syncback()

            return bool(self.info["login"]["valid"])

    def logout(self):
        """
        Invalidate the account timestamp so relogin will be forced next time.
        """
        self.sync()
        self.info["login"]["timestamp"] = 0
        self.syncback()

    # TODO: Recheck in 0.6.x
    def syncback(self):
        """
        Wrapper to directly sync self.info -> self.accounts[self.user]
        """
        return self.sync(reverse=True)

    # TODO: Recheck in 0.6.x
    def sync(self, reverse=False):
        """
        Sync self.accounts[self.user] -> self.info or self.info ->
        self.accounts[self.user] (if reverse is True)
        """
        if not self.user:
            return

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

    def relogin(self):
        return self.login()

    def reset(self):
        self.sync()

        def clear(x):
            return {} if isinstance(x, dict) else [] if is_sequence(x) else None

        self.info["data"] = {k: clear(v) for k, v in self.info["data"].items()}
        self.info["data"]["options"] = {"limit_dl": ["0"]}

        self.syncback()

    def get_info(self, refresh=True):
        """
        Retrieve account infos for a user, do **not** overwrite this method! just use
        it to retrieve infos in downloader plugins. see `grab_info`

        :return: dictionary with information
        """
        if not self.logged:
            if self.relogin():
                refresh = True
            else:
                refresh = False
                self.reset()

        if refresh and self.info["login"]["valid"]:
            self.log_info(
                self._("Grabbing account info for user `{}`...").format(self.user)
            )
            self.info = self._grab_info()

            self.syncback()

            self.log_debug(
                "Account info for user `{}`: {}".format(self.user, self.info)
            )

        return self.info

    def get_login(self, key=None, default=None):
        d = self.get_info()["login"]
        return d.get(key, default) if key else d

    def get_data(self, key=None, default=None):
        d = self.get_info()["data"]
        return d.get(key, default) if key else d

    def _grab_info(self):
        try:
            data = self.grab_info(
                self.user, self.info["login"]["password"], self.info["data"]
            )

            if data and isinstance(data, dict):
                self.info["data"].update(data)

        except NotImplementedError:
            self.log_error(
                self._("Error loading info for user `{}`").format(self.user),
                self._("Plugin is missing a function")
            )

        except Exception as exc:
            self.log_warning(
                self._("Error loading info for user `{}`").format(self.user), exc
            )

        finally:
            return self.info

    def grab_info(self, user, password, data):
        """
        This should be overwritten in account plugin and retrieving account information
        for user.

        :param user:
        :param password:
        :param data:
        :return:
        """
        raise NotImplementedError

    ###########################################################################
    # TODO: Recheck and move to `AccountManager` in 0.6.x ####################
    ###########################################################################

    @lock
    def init_accounts(self):
        accounts = dict(self.accounts)
        self.accounts.clear()

        for user, info in accounts.items():
            self.add(user, info["password"], info["options"])

    @lock
    def get_account_data(self, user, force=False):
        if force:
            self.accounts[user]["plugin"].get_info()

        return self.accounts[user]

    @lock
    def get_all_accounts(self, force=False):
        if force:
            self.init_accounts()  # TODO: Recheck in 0.6.x

        # NOTE: `init_accounts()` already calls get_account_data(user, True), avoid calling `get_info()` twice
        # NOTE: So force=False always here
        return [self.get_account_data(user, False) for user in self.accounts]

    # TODO: Remove in 0.6.x
    @lock
    def schedule_refresh(self, user, force=False):
        pass

    @lock
    def add(self, user, password=None, options={}):
        self.log_info(self._("Adding user `{}`...").format(user[:3] + "*" * 7))

        if user in self.accounts:
            self.log_error(
                self._("Error adding user `{}`").format(user),
                self._("User already exists"),
            )
            return False

        d = {
            "login": user,
            "options": options or {"limit_dl": ["0"]},
            "password": password or "",
            "plugin": self.pyload.account_manager.get_account_plugin(self.classname),
            "premium": None,
            "stats": [0, 0],  #: login_count, chosen_time
            "timestamp": 0,
            "trafficleft": None,
            "type": self.__name__,
            "valid": None,
            "validuntil": None,
        }

        u = self.accounts[user] = d
        result = u["plugin"].choose(user)
        u["plugin"].get_info()

        return result

    @lock
    def update_accounts(self, user, password=None, options={}):
        """
        Updates account and return true if anything changed.
        """
        if user in self.accounts:
            self.log_info(self._("Updating account info for user `{}`...").format(user))

            u = self.accounts[user]
            if password:
                u["password"] = password

            if options:
                u["options"].update(options)

            u["plugin"].relogin()

        else:
            self.add(user, password, options)

    @lock
    def remove_account(self, user):
        self.log_info(self._("Removing user `{}`...").format(user))
        self.accounts.pop(user, None)
        self.pyload.request_factory.remove_cookie_jar(self.classname, user)
        if user is self.user:
            self.choose()

    @lock
    def select(self):
        def hide(secret):
            hidden = secret[:3] + "*******"
            return hidden

        free_accounts = {}
        premium_accounts = {}

        for user in self.accounts:
            if not self.accounts[user]["plugin"].choose(user):
                continue

            info = self.accounts[user]["plugin"].get_info()
            data = info["data"]

            if not info["login"]["valid"]:
                continue

            if data["options"].get("time"):
                time_data = ""
                try:
                    time_data = data["options"]["time"][0]
                    start, end = time_data.split("-")

                    if not seconds.compare(start.split(":"), end.split(":")):
                        continue

                except Exception:
                    self.log_warning(
                        self._(
                            "Invalid time format `{}` for account `{}`, use 1:22-3:44"
                        ).format(hide(user), time_data)
                    )

            if data["trafficleft"] == 0:
                self.log_warning(
                    self._(
                        "Not using account `{}` because the account has no traffic left"
                    ).format(hide(user))
                )
                continue

            validuntil = -1 if not data["validuntil"] else data["validuntil"]
            if time.time() > validuntil > 0:
                self.log_warning(
                    self._(
                        "Not using account `{}` because the account has expired"
                    ).format(hide(user))
                )
                continue

            if data["premium"]:
                premium_accounts[user] = copy.copy(info)

            else:
                free_accounts[user] = copy.copy(info)

        account_list = list((premium_accounts or free_accounts).items())

        if not account_list:
            return None, None

        #: Choose the oldest used account
        chosen_account = sorted(account_list, key=lambda x: x[1]["login"]["stats"][1])[0]
        self.accounts[chosen_account[0]]["stats"][1] = time.time()

        self.log_debug("Using account {}".format(hide(chosen_account[0])))
        return chosen_account

    @lock
    def choose(self, user=None):
        """
        Choose a valid account.
        """
        if not user:
            user = self.select()[0]

        elif user not in self.accounts:
            self.log_error(
                self._("Error choosing user `{}`").format(user),
                self._("User does not exists"),
            )
            return False

        else:
            if self.req and user == self.user:
                return True

        if user is None:
            return False

        else:
            self.user = user
            self.info.clear()
            self.req.close()

            self.req = self.pyload.request_factory.get_request(
                self.classname, self.user
            )

            if not self.logged:
                self.relogin()

            return True

    def parse_traffic(self, size, unit=None):  #: returns bytes
        self.log_debug(f"Size: {size}", f"Unit: {unit or 'N/D'}")
        return parse.bytesize(size, unit or "byte")

    def fail_login(self, msg="Login handshake has failed"):
        return self.fail(msg)

    def skip_login(self, msg="Already signed in"):
        return self.skip(msg)
