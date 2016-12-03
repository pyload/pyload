# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.utils import to_bool
from pyload.Api import Api, RequirePerm, Permission, Conflict
from .ApiComponent import ApiComponent


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
    def getAccountInfo(self, aid, plugin, refresh=False):
        """ Returns :class:`AccountInfo` for a specific account

            :param refresh: reload account info
        """
        account = self.core.accountManager.getAccount(aid, plugin)

        # Admins can see and refresh accounts
        if not account or (self.primaryUID and self.primaryUID != account.owner):
            return None

        if refresh:
            # reload account in place
            account.getAccountInfo(True)

        return account.toInfoData()

    @RequirePerm(Permission.Accounts)
    def createAccount(self, plugin, loginname, password):
        """  Creates a new account

        :return class:`AccountInfo`
        """
        return self.core.accountManager.createAccount(plugin, loginname, password, self.user.true_primary).toInfoData()

    @RequirePerm(Permission.Accounts)
    def updateAccount(self, aid, plugin, loginname, password):
        """Updates loginname and password of an existent account

        :return: updated account info
        """
        return self.core.accountManager.updateAccount(aid, plugin, loginname, password, self.user).toInfoData()


    @RequirePerm(Permission.Accounts)
    def updateAccountInfo(self, account):
        """ Update account settings from :class:`AccountInfo` """
        inst = self.core.accountManager.getAccount(account.aid, account.plugin, self.user)
        if not inst:
            return

        inst.activated = to_bool(account.activated)
        inst.shared = to_bool(account.shared)
        inst.updateConfig(account.config)


    @RequirePerm(Permission.Accounts)
    def removeAccount(self, account):
        """Remove account from pyload.

        :param account: :class:`ÀccountInfo` instance
        """
        self.core.accountManager.removeAccount(account.aid, account.plugin, self.primaryUID)


if Api.extend(AccountApi):
    del AccountApi
