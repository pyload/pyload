# -*- coding: utf-8 -*-

from module.plugins.Addon import Addon
import ldap

class LDAPAuth(Addon):
    __name__ = "LDAPAuth"
    __category__ = "auth"
    __version__ = "0.1"
    __description__ = "Authenticates against an LDAP server"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("uri", "str", "URI of LDAP server", "ldap://localhost"),
                  ("base", "str", "base of LDAP tree", "ou=People,dc=example,dc=org"),
                  ("attr", "str", "attribute to check username against", "uid"),
                  ("tls", "bool", "use TLS (fails if not available)", "True")]
    __author_name__ = ("jplitza")
    __author_mail__ = ("janphilipp@litza.de")
        
    def checkAuth(self, username, password, remoteip = None):
        connection = ldap.initialize(self.getConfig("uri"))

        try:
            if self.getConfig("tls"):
                connection.start_tls_s()
            connection.simple_bind_s("%s=%s,%s" % 
                (self.getConfig("attr"), username, self.getConfig("base")), password)
            return username
        except ldap.INVALID_CREDENTIALS:
            return None
        except ldap.SERVER_DOWN:
            self.core.log.error("Could not establish connection to LDAP server '%s'", self.getConfig("uri"))
            return None
        except ldap.LDAPError, ex:
            self.core.log.error("Error binding to LDAP server '%s': %s", str(ex))
            return None
        finally:
            try:
                connection.unbind_s()
            except:
                pass
