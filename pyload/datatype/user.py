# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import unicode_literals
from builtins import str
from pyload.api import UserData, Permission, Role
from pyload.utils import bits_set


# TODO: activate user
# noinspection PyUnresolvedReferences
class User(UserData):

    @staticmethod
    def from_user_data(api, user):
        return User(api, user.uid, user.name, user.email, user.role, user.permission, user.folder,
                    user.traffic, user.dllimit, user.dlquota, user.hddquota, user.user, user.templatename)

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
        if isinstance(perms, str) and hasattr(Permission, perms):
            perms = getattr(Permission, perms)

        return bits_set(perms, self.permission)

    def has_role(self, role):
        if isinstance(role, str) and hasattr(Role, role):
            role = getattr(Role, role)

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
