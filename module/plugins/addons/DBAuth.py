# -*- coding: utf-8 -*-

from module.plugins.Addon import Addon

class DBAuth(Addon):
    __name__ = "DBAuth"
    __version__ = "0.1"
    __description__ = """Authenticate users using the pyload database"""
    __config__ = [("activated", "bool", "Activated", "True")]
    __author_name__ = ("jplitza")
    __author_mail__ = ("janphilipp@litza.de")
    
    def checkAuth(self, username, password, remoteip = None):
        """
        Checks whether the supplied credentials are correct.
        
        :param username: username of the user
        :param password: plaintext password of the user
        :return: The username to use if the authentication was successful, None otherwise
        """
        return username if self.core.db.checkAuth(username, password) != None else None

    @property
    def supportsAdding(self):
        return True