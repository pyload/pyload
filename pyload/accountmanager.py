# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import unicode_literals
from builtins import object
from threading import Lock
from random import choice

from pyload.Api import AccountInfo
from pyload.utils import lock, json


class AccountManager(object):
    """manages all accounts"""

    def __init__(self, core):
        """Constructor"""

        self.core = core
        self.lock = Lock()

        # PluginName mapped to list of account instances
        self.accounts = {}

        self.loadAccounts()

    def _createAccount(self, info, password, options):
        plugin = info.plugin
        loginname = info.loginname
        # Owner != None must be enforced
        if info.owner is None:
            raise ValueError("Owner must not be null")

        klass = self.core.pluginManager.loadClass("accounts", plugin)
        if not klass:
            self.core.log.warning(_("Account plugin %s not available") % plugin)
            raise ValueError("Account plugin %s not available" % plugin)

        if plugin not in self.accounts:
            self.accounts[plugin] = []

        self.core.log.debug("Create account %s:%s" % (plugin, loginname))

        # New account instance
        account = klass.fromInfoData(self, info, password, options)
        self.accounts[plugin].append(account)
        return account

    def loadAccounts(self):
        """loads all accounts available from db"""
        for info, password, options in self.core.db.loadAccounts():
            # put into options as used in other context
            options = json.loads(options) if options else {}
            try:
                self._createAccount(info, password, options)
            except Exception:
                self.core.log.error(_("Could not load account %s") % info)
                self.core.print_exc()

    def iterAccounts(self):
        """ yields login, account  for all accounts"""
        for plugin, accounts in self.accounts.items():
            for account in accounts:
                yield plugin, account

    def saveAccounts(self):
        """save all account information"""
        data = []
        for plugin, accounts in self.accounts.items():
            data.extend(
                [(acc.loginname, 1 if acc.activated else 0, 1 if acc.shared else 0, acc.password,
                  json.dumps(acc.options), acc.aid) for acc in
                 accounts])
        self.core.db.saveAccounts(data)

    def getAccount(self, aid, plugin, user=None):
        """ Find a account by specific user (if given) """
        if plugin in self.accounts:
            for acc in self.accounts[plugin]:
                if acc.aid == aid and (not user or acc.owner == user.true_primary):
                    return acc

    @lock
    def createAccount(self, plugin, loginname, password, uid):
        """ Creates a new account """

        aid = self.core.db.createAccount(plugin, loginname, password, uid)
        info = AccountInfo(aid, plugin, loginname, uid, activated=True)
        account = self._createAccount(info, password, {})
        account.scheduleRefresh()
        self.saveAccounts()

        self.core.eventManager.dispatchEvent("account:created", account.toInfoData())
        return account

    @lock
    def updateAccount(self, aid, plugin, loginname, password, user):
        """add or update account"""
        account = self.getAccount(aid, plugin, user)
        if not account:
            return

        if account.setLogin(loginname, password):
            self.saveAccounts()
            account.scheduleRefresh(force=True)

        self.core.eventManager.dispatchEvent("account:updated", account.toInfoData())
        return account

    @lock
    def removeAccount(self, aid, plugin, uid):
        """remove account"""
        if plugin in self.accounts:
            for acc in self.accounts[plugin]:
                # admins may delete accounts
                if acc.aid == aid and (not uid or acc.owner == uid):
                    self.accounts[plugin].remove(acc)
                    self.core.db.removeAccount(aid)
                    self.core.evm.dispatchEvent("account:deleted", aid, user=uid)
                    break

    @lock
    def selectAccount(self, plugin, user):
        """ Determines suitable plugins and select one """
        if plugin in self.accounts:
            uid = user.true_primary if user else None
            # TODO: temporary allowed None user
            accs = [x for x in self.accounts[plugin] if x.isUsable() and (x.shared or uid is None or x.owner == uid)]
            if accs: return choice(accs)

    @lock
    def getAllAccounts(self, uid):
        """ Return account info for every visible account """
        # filter by owner / shared, but admins see all accounts
        accounts = []
        for plugin, accs in self.accounts.items():
            accounts.extend([acc for acc in accs if acc.shared or not uid or acc.owner == uid])

        return accounts

    def refreshAllAccounts(self):
        """ Force a refresh of every account """
        for p in self.accounts.values():
            for acc in p:
                acc.getAccountInfo(True)
