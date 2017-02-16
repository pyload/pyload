# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from future import standard_library

from pyload.api import Api, Permission, require_perm
from pyload.api.base import BaseApi

standard_library.install_aliases()


class UserApi(BaseApi):
    """
    Api methods to retrieve user profile and manage users.
    """

    @require_perm(Permission.All)
    def get_user_data(self):
        """
        Retrieves :class:`UserData` for the currently logged in user.
        """
        raise NotImplementedError

    @require_perm(Permission.All)
    def set_password(self, username, old_password, new_password):
        """
        Changes password for specific user.
        User can only change their password.
        Admins can change every password!
        """
        raise NotImplementedError

    def get_all_user_data(self):
        """
        Retrieves :class:`UserData` of all exisitng users.
        """
        raise NotImplementedError

    def add_user(self, username, password):
        """
        Adds an user to the db.

        :param username: desired username
        :param password: password for authentication
        """
        raise NotImplementedError

    def update_user_data(self, data):
        """
        Change parameters of user account.
        """
        raise NotImplementedError

    def remove_user(self, uid):
        """
        Removes user from the db.

        :param uid: users uid.
        """
        raise NotImplementedError


if Api.extend(UserApi):
    del UserApi
