#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2013 pyLoad Team
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

import re
from types import MethodType

from remote.apitypes import *

# contains function names mapped to their permissions
# unlisted functions are for admins only
perm_map = {}

# decorator only called on init, never initialized, so has no effect on runtime
def RequirePerm(bits):
    class _Dec(object):
        def __new__(cls, func, *args, **kwargs):
            perm_map[func.__name__] = bits
            return func

    return _Dec

urlmatcher = re.compile(r"((https?|ftps?|xdcc|sftp):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+\-=\\\.&]*)", re.IGNORECASE)

stateMap = {
    DownloadState.All: frozenset(getattr(DownloadStatus, x) for x in dir(DownloadStatus) if not x.startswith("_")),
    DownloadState.Finished: frozenset((DownloadStatus.Finished, DownloadStatus.Skipped)),
    DownloadState.Unfinished: None, # set below
    DownloadState.Failed: frozenset((DownloadStatus.Failed, DownloadStatus.TempOffline, DownloadStatus.Aborted)),
    DownloadState.Unmanaged: None, #TODO
}

stateMap[DownloadState.Unfinished] = frozenset(stateMap[DownloadState.All].difference(stateMap[DownloadState.Finished]))

def state_string(state):
    return ",".join(str(x) for x in stateMap[state])

from datatypes.User import User

class Api(Iface):
    """
    **pyLoads API**

    This is accessible either internal via core.api, websocket backend or json api.

    see Thrift specification file remote/thriftbackend/pyload.thrift\
    for information about data structures and what methods are usable with rpc.

    Most methods requires specific permissions, please look at the source code if you need to know.\
    These can be configured via web interface.
    Admin user have all permissions, and are the only ones who can access the methods with no specific permission.
    """

    EXTERNAL = Iface  # let the json api know which methods are external
    EXTEND = False  # only extendable when set too true

    def __init__(self, core):
        self.core = core
        self.user_apis = {}

    @property
    def user(self):
        return None #TODO return default user?

    @property
    def primaryUID(self):
        return self.user.primary if self.user else None

    @classmethod
    def initComponents(cls):
        # Allow extending the api
        # This prevents unintentionally registering of the components,
        # but will only work once when they are imported
        cls.EXTEND = True
        # Import all Api modules, they register themselves.
        import module.api
        # they will vanish from the namespace afterwards


    @classmethod
    def extend(cls, api):
        """Takes all params from api and extends cls with it.
            api class can be removed afterwards

        :param api: Class with methods to extend
        """
        if cls.EXTEND:
            for name, func in api.__dict__.iteritems():
                if name.startswith("_"): continue
                setattr(cls, name, MethodType(func, None, cls))

        return cls.EXTEND

    def withUserContext(self, uid):
        """ Returns a proxy version of the api, to call method in user context

        :param uid: user or userData instance or uid
        :return: :class:`UserApi`
        """
        if isinstance(uid, User):
            uid = uid.uid

        if uid not in self.user_apis:
            user = self.core.db.getUserData(uid=uid)
            if not user: #TODO: anonymous user?
                return None

            self.user_apis[uid] = UserApi(self.core, User.fromUserData(self, user))

        return self.user_apis[uid]


    #############################
    #  Auth+User Information
    #############################

    # TODO

    @RequirePerm(Permission.All)
    def login(self, username, password, remoteip=None):
        """Login into pyLoad, this **must** be called when using rpc before any methods can be used.

        :param username:
        :param password:
        :param remoteip: Omit this argument, its only used internal
        :return: bool indicating login was successful
        """
        return True if self.checkAuth(username, password, remoteip) else False

    def checkAuth(self, username, password, remoteip=None):
        """Check authentication and returns details

        :param username:
        :param password:
        :param remoteip:
        :return: dict with info, empty when login is incorrect
        """
        
        self.core.log.info(_("User '%s' tries to log in") % username)
        
        real_username = None
        for plugin in addonManager.activePlugins():
            if plugin.__category__ == "auth":
                self.core.log.debug("Trying plugin %s for logging in %s" % (plugin.__name__, username))
                try:
                    real_username = plugin.checkAuth(username, password, remoteip)
                except:
                    self.core.print_exc()
                if real_username:
                    self.core.log.debug("Login for %s succeeded with plugin %s" % (username, plugin.__name__))
                    break
        # fall back to default auth against internal database
        else:
            self.core.log.debug("Trying internal authentication for logging in %s" % username)
            if self.core.db.checkAuth(username, password) != None:
                self.core.log.debug("Login for %s succeeded with internal authentication" % username)
                real_username = username

        userdata = self.core.db.getUserData(real_username)
        if not userdata and real_username:
            self.core.db.addUser(real_username, None)
            userdata = self.core.db.getUserData(real_username)
        return userdata

    def isAuthorized(self, func, user):
        """checks if the user is authorized for specific method

        :param func: function name
        :param user: `User`
        :return: boolean
        """
        if user.isAdmin():
            return True
        elif func in perm_map and user.hasPermission(perm_map[func]):
            return True
        else:
            return False

    # TODO
    @RequirePerm(Permission.All)
    def getUserData(self, username, password):
        """similar to `checkAuth` but returns UserData thrift type """
        user = self.checkAuth(username, password)
        if not user:
            raise UserDoesNotExists(username)

        return user.toUserData()

    def getAllUserData(self):
        """returns all known user and info"""
        return self.core.db.getAllUserData()

    def changePassword(self, username, oldpw, newpw):
        """ changes password for specific user """
        return self.core.db.changePassword(username, oldpw, newpw)

    def setUserPermission(self, user, permission, role):
        self.core.db.setPermission(user, permission)
        self.core.db.setRole(user, role)


class UserApi(Api):
    """  Proxy object for api that provides all methods in user context """

    def __init__(self, core, user):
        # No need to init super class
        self.core = core
        self._user = user

    def withUserContext(self, uid):
        raise Exception("Not allowed")

    @property
    def user(self):
        return self._user
