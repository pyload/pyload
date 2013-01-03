#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2012 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################


from module.Api import UserData, Permission, Role, has_permission

#TODO: activate user
#noinspection PyUnresolvedReferences
class User(UserData):

    @staticmethod
    def fromUserData(api, user):
        return User(api, user.uid, user.name, user.email, user.role, user.permission, user.folder,
            user.traffic, user.dllimit, user.dlquota, user.hddquota, user.user, user.templateName)

    def __init__(self, api,  *args, **kwargs):
        UserData.__init__(self, *args, **kwargs)
        self.api = api


    def toUserData(self):
        # TODO
        return UserData()

    def hasPermission(self, perms):
        """  Accepts permission bit or name  """

        if isinstance(perms, basestring) and hasattr(Permission, perms):
            perms = getattr(Role, perms)

        return has_permission(self.permission, perms)

    def hasRole(self, role):
        if isinstance(role, basestring) and hasattr(Role, role):
            role = getattr(Role, role)

        return self.role == role

    def isAdmin(self):
        return self.hasRole(Role.Admin)

    @property
    def primary(self):
        """ Primary user id, Internal user handle used for most operations
        Secondary user account share id with primary user. Only Admins have no primary id. """
        if self.hasRole(Role.Admin):
            return None
        return self.user if self.user else self.uid