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


from module.Api import UserData

#noinspection PyUnresolvedReferences
class User(UserData):

    @staticmethod
    def fromUserData(manager, user):
        return User(manager, user.uid, user.name, user.email, user.role, user.permission, user.folder,
            user.traffic, user.dllimit, user.dlquota, user.hddquota, user.user, user.templateName)

    def __init__(self, manager,  *args):
        UserData.__init__(*args)
        self.m = manager

