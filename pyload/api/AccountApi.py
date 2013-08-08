#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyload.Api import Api, RequirePerm, Permission, Conflict
from ApiComponent import ApiComponent


class AccountApi(ApiComponent):
    """ All methods to control accounts """

    @RequirePerm(Permission.All)
    def getAccountTypes(self):
        """All available account types.

        :return: string list
        """
        return self.core.pluginManager.getPlugins("accounts").keys()

    @RequirePerm(Permission.Accounts)
    def getAccounts(self):
        """Get information about all entered accounts.

        :return: list of `AccountInfo`
        """
        accounts = self.core.accountManager.getAllAccounts(self.primaryUID)
        return [acc.toInfoData() for acc in accounts]

    @RequirePerm(Permission.Accounts)
    def getAccountInfo(self, plugin, loginname, refresh=False):
        """ Returns :class:`AccountInfo` for a specific account

            :param refresh: reload account info
        """
        account = self.core.accountManager.getAccount(plugin, loginname)

        # Admins can see and refresh accounts
        if not account or (self.primaryUID and self.primaryUID != account.owner):
            return None

        if refresh:
            # reload account in place
            account.getAccountInfo(True)

        return account.toInfoData()

    @RequirePerm(Permission.Accounts)
    def updateAccount(self, plugin, loginname, password):
        """Creates an account if not existent or updates the password

        :return: newly created or updated account info
        """
        return self.core.accountManager.updateAccount(plugin, loginname, password, self.user).toInfoData()


    @RequirePerm(Permission.Accounts)
    def updateAccountInfo(self, account):
        """ Update account settings from :class:`AccountInfo` """
        #TODO

    @RequirePerm(Permission.Accounts)
    def removeAccount(self, account):
        """Remove account from pyload.

        :param account: :class:`ÀccountInfo` instance
        """
        self.core.accountManager.removeAccount(account.plugin, account.loginname, self.primaryUID)


if Api.extend(AccountApi):
    del AccountApi