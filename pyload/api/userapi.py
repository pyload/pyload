# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.Api import Api, require_perm, Permission

from .apicomponent import ApiComponent


class UserApi(ApiComponent):
    """ Api methods to retrieve user profile and manage users. """

    @require_perm(Permission.All)
    def get_user_data(self):
        """ Retrieves :class:`UserData` for the currently logged in user. """

    @require_perm(Permission.All)
    def set_password(self, username, old_password, new_password):
        """ Changes password for specific user. User can only change their password.
        Admins can change every password! """

    def get_all_user_data(self):
        """ Retrieves :class:`UserData` of all exisitng users."""

    def add_user(self, username, password):
        """ Adds an user to the db.

        :param username: desired username
        :param password: password for authentication
        """

    def update_user_data(self, data):
        """ Change parameters of user account.  """

    def remove_user(self, uid):
        """ Removes user from the db.

        :param uid: users uid
        """


if Api.extend(UserApi):
    del UserApi
