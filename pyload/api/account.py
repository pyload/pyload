# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.utils import to_bool
from pyload.api import Api, require_perm, Permission, Conflict
from pyload.api.base import BaseApi


class AccountApi(BaseApi):
    """ All methods to control accounts """

    @require_perm(Permission.All)
    def get_account_types(self):
        """All available account types.

        :return: string list
        """
        return list(self.pyload.pluginmanager.get_plugins("account").keys())

    @require_perm(Permission.Accounts)
    def get_accounts(self):
        """Get information about all entered accounts.

        :return: list of `AccountInfo`
        """
        accounts = self.pyload.accountmanager.get_all_accounts(self.primary_uid)
        return [acc.to_info_data() for acc in accounts]

    @require_perm(Permission.Accounts)
    def get_account_info(self, aid, plugin, refresh=False):
        """ Returns :class:`AccountInfo` for a specific account

            :param refresh: reload account info
        """
        account = self.pyload.accountmanager.get_account(aid, plugin)

        # Admins can see and refresh accounts
        if not account or (self.primary_uid and self.primary_uid != account.owner):
            return None

        if refresh:
            # reload account in place
            account.get_account_info(True)

        return account.to_info_data()

    @require_perm(Permission.Accounts)
    def create_account(self, plugin, loginname, password):
        """  Creates a new account

        :return class:`AccountInfo`
        """
        return self.pyload.accountmanager.create_account(plugin, loginname, password, self.user.true_primary).to_info_data()

    @require_perm(Permission.Accounts)
    def update_account(self, aid, plugin, loginname, password):
        """Updates loginname and password of an existent account

        :return: updated account info
        """
        return self.pyload.accountmanager.update_account(aid, plugin, loginname, password, self.user).to_info_data()


    @require_perm(Permission.Accounts)
    def update_account_info(self, account):
        """ Update account settings from :class:`AccountInfo` """
        inst = self.pyload.accountmanager.get_account(account.aid, account.plugin, self.user)
        if not inst:
            return

        inst.activated = to_bool(account.activated)
        inst.shared = to_bool(account.shared)
        inst.update_config(account.config)


    @require_perm(Permission.Accounts)
    def remove_account(self, account):
        """Remove account from pyload.

        :param account: :class:`ÀccountInfo` instance
        """
        self.pyload.accountmanager.remove_account(account.aid, account.plugin, self.primary_uid)


if Api.extend(AccountApi):
    del AccountApi
