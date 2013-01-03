#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.Api import Api, RequirePerm, Permission

from ApiComponent import ApiComponent

class AccountApi(ApiComponent):
    """ All methods to control accounts """

    @RequirePerm(Permission.Accounts)
    def getAccounts(self, refresh):
        """Get information about all entered accounts.

        :param refresh: reload account info
        :return: list of `AccountInfo`
        """
        accs = self.core.accountManager.getAllAccounts(refresh)
        accounts = []
        for plugin in accs.itervalues():
            accounts.extend(plugin.values())

        return accounts

    @RequirePerm(Permission.All)
    def getAccountTypes(self):
        """All available account types.

        :return: string list
        """
        return self.core.pluginManager.getPlugins("accounts").keys()

    @RequirePerm(Permission.Accounts)
    def updateAccount(self, plugin, account, password=None, options={}):
        """Changes pw/options for specific account."""
        self.core.accountManager.updateAccount(plugin, account, password, options)

    @RequirePerm(Permission.Accounts)
    def removeAccount(self, plugin, account):
        """Remove account from pyload.

        :param plugin: pluginname
        :param account: accountname
        """
        self.core.accountManager.removeAccount(plugin, account)


if Api.extend(AccountApi):
    del AccountApi