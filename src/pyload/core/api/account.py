# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()

from ..datatype.init import Permission
from .base import BaseApi
from .init import Api, requireperm


class AccountApi(BaseApi):
    """
    All methods to control accounts.
    """
    # __slots__ = []

    @requireperm(Permission.All)
    def get_account_types(self):
        """
        All available account types.

        :return: string list
        """
        return list(self.pyload.pgm.get_plugins("account").keys())

    @requireperm(Permission.Accounts)
    def get_accounts(self):
        """
        Get information about all entered accounts.

        :return: list of `AccountInfo`
        """
        accounts = self.pyload.acm.get_all_accounts(self.primary_uid)
        return [acc.to_info_data() for acc in accounts]

    @requireperm(Permission.Accounts)
    def get_account_info(self, aid, plugin, refresh=False):
        """
        Returns :class:`AccountInfo` for a specific account

        :param refresh: reload account info
        """
        account = self.pyload.acm.get_account(aid, plugin)

        # Admins can see and refresh accounts
        if not account or (
                self.primary_uid and self.primary_uid != account.owner):
            return None

        if refresh:
            # reload account in place
            account.get_account_info(True)

        return account.to_info_data()

    @requireperm(Permission.Accounts)
    def create_account(self, plugin, loginname, password):
        """
        Creates a new account

        :return class:`AccountInfo`
        """
        return self.pyload.acm.create_account(
            plugin, loginname, password, self.user.true_primary).to_info_data()

    @requireperm(Permission.Accounts)
    def update_account(self, aid, plugin, loginname, password):
        """
        Updates loginname and password of an existent account

        :return: updated account info
        """
        return self.pyload.acm.update_account(
            aid, plugin, loginname, password, self.user).to_info_data()

    @requireperm(Permission.Accounts)
    def update_account_info(self, account):
        """
        Update account settings from :class:`AccountInfo`.
        """
        inst = self.pyload.acm.get_account(
            account.aid, account.plugin, self.user)
        if not inst:
            return None

        inst.activated = bool(account.activated)
        inst.shared = bool(account.shared)
        inst.update_config(account.config)

    @requireperm(Permission.Accounts)
    def remove_account(self, account):
        """
        Remove account from core.

        :param account: :class:`ÀccountInfo` instance
        """
        self.pyload.acm.remove_account(
            account.aid, account.plugin, self.primary_uid)
