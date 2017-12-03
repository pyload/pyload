# -*- coding: utf-8 -*-
"""
  Backend allowing ANY user to log into pyload.
  This is to be used ONLY when server is restricted to local connections.

  @author: Hadrien Theveneau
"""

from DatabaseBackend import style

class Dummy_UserMethods():
    dummy_user = {"id": 1, "name": "User", "role": 0,
                  "permission": 1023, "template": None, "email": None}

    @style.queue
    def checkAuth(db, user, password):
        return Dummy_UserMethods.dummy_user
    
    @style.queue
    def addUser(db, user, password):
        pass
    
    @style.queue
    def changePassword(db, user, oldpw, newpw):
        pass
    
    @style.async
    def setPermission(db, user, perms):
        pass
    
    @style.async
    def setRole(db, user, role):
        pass
    
    @style.queue
    def listUsers(db):
        return [self.dummy_user]
    
    @style.queue
    def getAllUserData(db):
        return {Dummy_UserMethods.dummy_user['name']: Dummy_UserMethods.dummy_user}
    
    @style.queue
    def removeUser(db, user):
        pass

