# -*- coding: utf-8 -*-

import os
import shutil
from threading import Lock

from ..utils.old import lock
from .event_manager import AccountUpdateEvent

# MANAGER VERSION
__version__ = 1


class AccountManager:
    """
    manages all accounts.
    """

    # ----------------------------------------------------------------------
    def __init__(self, core):
        """
        Constructor.
        """
        self.pyload = core
        self._ = core._
        self.lock = Lock()

        # TODO: Recheck
        configdir = os.path.join(core.userdir, "settings")
        os.makedirs(configdir, exist_ok=True)

        self.configpath = os.path.join(configdir, "accounts.conf")

        self.init_plugins()
        self.save_accounts()  #: save to add categories to conf

    def init_plugins(self):
        self.accounts = {}  #: key = ( plugin )
        self.plugins = {}

        self.init_account_plugins()
        self.load_accounts()

    def get_account_plugin(self, plugin):
        """
        get account instance for plugin or None if anonymous.
        """
        if plugin in self.accounts:
            if plugin not in self.plugins:
                self.plugins[plugin] = self.pyload.plugin_manager.load_class(
                    "account", plugin
                )(self, self.accounts[plugin])

            return self.plugins[plugin]
        else:
            return None

    def get_account_plugins(self):
        """
        get all account instances.
        """
        plugins = []
        for plugin in self.accounts.keys():
            plugins.append(self.get_account_plugin(plugin))

        return plugins

    # ----------------------------------------------------------------------

    def load_accounts(self):
        """
        loads all accounts available.
        """
        if not os.path.exists(self.configpath):
            with open(self.configpath, mode="w") as fp:
                fp.write(f"version: {__version__}")

        with open(self.configpath) as fp:
            content = fp.readlines()
            version = content[0].split(":")[1].strip() if content else ""

        if not version or int(version) < __version__:
            shutil.copy(self.configpath, "accounts.backup")
            with open(self.configpath, mode="w") as fp:
                fp.write(f"version: {__version__}")
            self.pyload.log.warning(
                self._("Account settings deleted, due to new config format.")
            )
            return

        plugin = ""
        name = ""

        for line in content[1:]:
            line = line.strip()

            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith("version"):
                continue

            if line.endswith(":") and line.count(":") == 1:
                plugin = line[:-1]
                self.accounts[plugin] = {}

            elif line.startswith("@"):
                try:
                    option = line[1:].split()
                    self.accounts[plugin][name]["options"][option[0]] = (
                        []
                        if len(option) < 2
                        else ([option[1]] if len(option) < 3 else option[1:])
                    )
                except Exception:
                    pass

            elif ":" in line:
                name, sep, pw = line.partition(":")
                self.accounts[plugin][name] = {
                    "password": pw,
                    "options": {},
                    "valid": True,
                }

    # ----------------------------------------------------------------------

    def save_accounts(self):
        """
        save all account information.
        """
        with open(self.configpath, mode="w") as fp:
            fp.write(f"version: {__version__}\n")

            for plugin, accounts in self.accounts.items():
                fp.write("\n")
                fp.write(plugin + ":\n")

                for name, data in accounts.items():
                    pw = data["password"]
                    fp.write(f"\n\t{name}:{pw}\n")
                    if data["options"]:
                        for option, values in data["options"].items():
                            line = " ".join(values)
                            fp.write(f"\t@{option} {line}\n")
            os.chmod(fp.name, 0o600)

    # ----------------------------------------------------------------------

    def init_account_plugins(self):
        """
        init names.
        """
        for name in self.pyload.plugin_manager.get_account_plugins():
            self.accounts[name] = {}

    @lock
    def update_account(self, plugin, user, password=None, options={}):
        """
        add or update account.
        """
        if plugin in self.accounts:
            p = self.get_account_plugin(plugin)
            updated = p.update_accounts(user, password, options)
            # since accounts is a ref in plugin self.accounts doesnt need to be
            # updated here

            self.save_accounts()
            if updated:
                p.schedule_refresh(user, force=False)

    @lock
    def remove_account(self, plugin, user):
        """
        remove account.
        """
        if plugin in self.accounts:
            p = self.get_account_plugin(plugin)
            p.remove_account(user)

            self.save_accounts()

    @lock
    def get_account_infos(self, force=True, refresh=False):
        data = {}

        if refresh:
            self.pyload.scheduler.add_job(
                0, self.pyload.account_manager.get_account_infos
            )
            force = False

        for p in self.accounts.keys():
            if self.accounts[p]:
                p = self.get_account_plugin(p)
                data[p.__name__] = p.get_all_accounts(force)
            else:
                data[p] = []
        e = AccountUpdateEvent()
        self.pyload.event_manager.add_event(e)
        return data

    def send_change(self):
        e = AccountUpdateEvent()
        self.pyload.event_manager.add_event(e)
