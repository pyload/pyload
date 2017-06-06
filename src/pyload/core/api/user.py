# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from ..datatype.init import Permission
from .base import BaseApi
from .init import requireperm

standard_library.install_aliases()


class UserApi(BaseApi):
    """
    Api methods to retrieve user profile and manage users.
    """
    @requireperm(Permission.All)
    def get_user_data(self):
        """
        Retrieves :class:`UserData` for the currently logged in user.
        """
        raise NotImplementedError

    @requireperm(Permission.All)
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
