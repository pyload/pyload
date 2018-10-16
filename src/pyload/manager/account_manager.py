# -*- coding: utf-8 -*-
# @author: RaNaN

import os
import shutil
from builtins import _, object, str
from threading import Lock

from pyload.manager.event_manager import AccountUpdateEvent
from pyload.utils.utils import chmod, lock

# MANAGER VERSION
__version__ = 1


class AccountManager(object):
    """
    manages all accounts.
    """

    # ----------------------------------------------------------------------
    def __init__(self, core):
        """
        Constructor.
        """

        self.pyload = core
        self.lock = Lock()

        self.initPlugins()
        self.saveAccounts()  # save to add categories to conf

    def initPlugins(self):
        self.accounts = {}  # key = ( plugin )
        self.plugins = {}

        self.initAccountPlugins()
        self.loadAccounts()

    def getAccountPlugin(self, plugin):
        """
        get account instance for plugin or None if anonymous.
        """
        if plugin in self.accounts:
            if plugin not in self.plugins:
                self.plugins[plugin] = self.pyload.pluginManager.loadClass(
                    "accounts", plugin
                )(self, self.accounts[plugin])

            return self.plugins[plugin]
        else:
            return None

    def getAccountPlugins(self):
        """
        get all account instances.
        """

        plugins = []
        for plugin in self.accounts.keys():
            plugins.append(self.getAccountPlugin(plugin))

        return plugins

    # ----------------------------------------------------------------------

    def loadAccounts(self):
        """
        loads all accounts available.
        """

        if not os.path.exists("accounts.conf"):
            with open("accounts.conf", "w") as f:
                f.write("version: {}".format(__version__))

        with open("accounts.conf") as f:
            content = f.readlines()
            version = content[0].split(":")[1].strip() if content else ""

        if not version or int(version) < __version__:
            shutil.copy("accounts.conf", "accounts.backup")
            with open("accounts.conf", "w") as f:
                f.write("version: {}".format(__version__))
            self.pyload.log.warning(
                _("Account settings deleted, due to new config format.")
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

    def saveAccounts(self):
        """
        save all account information.
        """

        with open("accounts.conf", "w") as f:
            f.write("version: {}\n".format(__version__)

            for plugin, accounts in self.accounts.items():
                f.write("\n")
                f.write(plugin + ":\n")

                for name, data in accounts.items():
                    f.write("\n\t{}:{}\n".format(name, data["password"]))
                    if data["options"]:
                        for option, values in data["options"].items():
                            f.write("\t@{} {}\n".format(option, " ".join(values)))
        chmod(f.name, 0o600)

    # ----------------------------------------------------------------------

    def initAccountPlugins(self):
        """
        init names.
        """
        for name in self.pyload.pluginManager.getAccountPlugins():
            self.accounts[name] = {}

    @lock
    def updateAccount(self, plugin, user, password=None, options={}):
        """
        add or update account.
        """
        if plugin in self.accounts:
            p = self.getAccountPlugin(plugin)
            updated = p.updateAccounts(user, password, options)
            # since accounts is a ref in plugin self.accounts doesnt need to be
            # updated here

            self.saveAccounts()
            if updated:
                p.scheduleRefresh(user, force=False)

    @lock
    def removeAccount(self, plugin, user):
        """
        remove account.
        """

        if plugin in self.accounts:
            p = self.getAccountPlugin(plugin)
            p.removeAccount(user)

            self.saveAccounts()

    @lock
    def getAccountInfos(self, force=True, refresh=False):
        data = {}

        if refresh:
            self.pyload.scheduler.addJob(0, self.pyload.accountManager.getAccountInfos)
            force = False

        for p in self.accounts.keys():
            if self.accounts[p]:
                p = self.getAccountPlugin(p)
                data[p.__name__] = p.getAllAccounts(force)
            else:
                data[p] = []
        e = AccountUpdateEvent()
        self.pyload.pullManager.addEvent(e)
        return data

    def sendChange(self):
        e = AccountUpdateEvent()
        self.pyload.pullManager.addEvent(e)
