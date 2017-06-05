# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

from future import standard_library

from pyload.utils.check import bitset

from .init import BaseObject, ExceptionObject, Permission

try:
    from enum import IntEnum
except ImportError:
    from aenum import IntEnum

standard_library.install_aliases()


class Role(IntEnum):
    Admin = 0
    User = 1


class UserDoesNotExist(ExceptionObject):

    __slots__ = ['user']

    def __init__(self, user=None):
        self.user = user


class UserData(BaseObject):

    __slots__ = ['uid', 'name', 'email', 'role', 'permission', 'folder',
                 'traffic', 'dllimit', 'dlquota', 'hddquota', 'user',
                 'templatename']

    def __init__(self, uid=None, name=None, email=None, role=None,
                 permission=None, folder=None, traffic=None, dllimit=None,
                 dlquota=None, hddquota=None, user=None, templatename=None):
        self.uid = uid
        self.name = name
        self.email = email
        self.role = role
        self.permission = permission
        self.folder = folder
        self.traffic = traffic
        self.dllimit = dllimit
        self.dlquota = dlquota
        self.hddquota = hddquota
        self.user = user
        self.templatename = templatename


# TODO: activate user
# noinspection PyUnresolvedReferences
class User(UserData):

    __slots__ = ['api']

    @staticmethod
    def from_user_data(api, user):
        return User(
            api, user.uid, user.name, user.email, user.role, user.permission,
            user.folder, user.traffic, user.dllimit, user.dlquota, user.
            hddquota, user.user, user.templatename)

    def __init__(self, api, *args, **kwargs):
        UserData.__init__(self, *args, **kwargs)
        self.api = api

    def to_user_data(self):
        # TODO
        return UserData()

    def has_permission(self, perms):
        """
        Accepts permission bit or name.
        """
        try:
            perms = getattr(Permission, perms)
        except Exception:
            pass
        return bitset(perms, self.permission)

    def has_role(self, role):
        try:
            role = getattr(Role, role)
        except Exception:
            pass
        return self.role == role

    def has_access(self, obj):
        return self.primary is None or obj.owner == self.true_primary

    def is_admin(self):
        return self.has_role(Role.Admin)

    @property
    def primary(self):
        """
        Primary user id, Internal user handle used for most operations.
        Secondary user account share id with primary user.
        Only Admins have no primary id.
        """
        if self.has_role(Role.Admin):
            return None
        return self.true_primary

    @property
    def true_primary(self):
        """
        Primary handle that does not distinguish admin accounts.
        """
        return self.user if self.user else self.uid
