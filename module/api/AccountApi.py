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
            accounts.extend([acc.toInfoData() for acc in plugin.values()])

        return accounts

    @RequirePerm(Permission.All)
    def getAccountTypes(self):
        """All available account types.

        :return: string list
        """
        return self.core.pluginManager.getPlugins("accounts").keys()

    @RequirePerm(Permission.Accounts)
    def updateAccount(self, plugin, login, password):
        """Changes pw/options for specific account."""
        # TODO: options
        self.core.accountManager.updateAccount(plugin, login, password, {})

    def updateAccountInfo(self, account):
        """ Update account from :class:`AccountInfo` """
        #TODO

    @RequirePerm(Permission.Accounts)
    def removeAccount(self, account):
        """Remove account from pyload.

        :param account: :class:`ÀccountInfo` instance
        """
        self.core.accountManager.removeAccount(account.plugin, account.loginname)


if Api.extend(AccountApi):
    del AccountApi