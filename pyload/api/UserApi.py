#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from pyload.Api import Api, RequirePerm, Permission

from .ApiComponent import ApiComponent

class UserApi(ApiComponent):
    """ Api methods to retrieve user profile and manage users. """

    @RequirePerm(Permission.All)
    def getUserData(self):
        """ Retrieves :class:`UserData` for the currently logged in user. """

    @RequirePerm(Permission.All)
    def setPassword(self, username, old_password, new_password):
        """ Changes password for specific user. User can only change their password.
        Admins can change every password! """

    def getAllUserData(self):
        """ Retrieves :class:`UserData` of all exisitng users."""

    def addUser(self, username, password):
        """ Adds an user to the db.

        :param username: desired username
        :param password: password for authentication
        """

    def updateUserData(self, data):
        """ Change parameters of user account.  """

    def removeUser(self, uid):
        """ Removes user from the db.

        :param uid: users uid
        """


if Api.extend(UserApi):
    del UserApi
