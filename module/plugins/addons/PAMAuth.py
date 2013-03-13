# -*- coding: utf-8 -*-

from DBAuth import DBAuth
import PAM

class PAMAuth(DBAuth):
    __name__ = "PAMAuth"
    __version__ = "0.1"
    __description__ = """Authenticates against the local PAM service
    
    If you are running pyLoad as non-root (and you should!), you can use this
    plugin only to authenticate as the user pyLoad runs as."""
    __config__ = [("activated", "bool", "Activated", "True"),
                  ("service", "str", "PAM service name to use", "passwd")]
    __author_name__ = ("jplitza")
    __author_mail__ = ("janphilipp@litza.de")
    
    def checkAuth(self, username, password, remoteip = None):
        def pam_conv(auth, query_list, userData):
            resp = []
            for item in query_list:
                if item[1] == PAM.PAM_PROMPT_ECHO_OFF:
                    resp.append((password, 0))
                else:
                    return None
            return resp
        
        auth = PAM.pam()
        auth.start(self.getConfig("service"))
        auth.set_item(PAM.PAM_USER, username)
        auth.set_item(PAM.PAM_CONV, pam_conv)
        try:
            auth.authenticate()
            auth.acct_mgmt()
        except PAM.error:
            return None
        return username
    
    @property
    def supportsAdding(self):
        return False