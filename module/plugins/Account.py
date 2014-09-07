# -*- coding: utf-8 -*-

from random import choice
from time import time
from traceback import print_exc
from threading import RLock

from module.plugins.Plugin import Base
from module.utils import compare_time, parseFileSize, lock


class WrongPassword(Exception):
    pass


class Account(Base):
    """
    Base class for every Account plugin.
    Just overwrite `login` and cookies will be stored and account becomes accessible in\
    associated hoster plugin. Plugin should also provide `loadAccountInfo`
    """
    __name__ = "Account"
    __type__ = "account"
    __version__ = "0.3"

    __description__ = """Base account plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"

    #: after that time (in minutes) pyload will relogin the account
    login_timeout = 10 * 60
    #: after that time (in minutes) account data will be reloaded
    info_threshold = 10 * 60


    def __init__(self, manager, accounts):
        Base.__init__(self, manager.core)

        self.manager = manager
        self.accounts = {}
        self.infos = {} # cache for account information
        self.lock = RLock()

        self.timestamps = {}
        self.setAccounts(accounts)
        self.init()

    def init(self):
        pass

    def login(self, user, data, req):
        """login into account, the cookies will be saved so user can be recognized

        :param user: loginname
        :param data: data dictionary
        :param req: `Request` instance
        """
        pass

    @lock
    def _login(self, user, data):
        # set timestamp for login
        self.timestamps[user] = time()

        req = self.getAccountRequest(user)
        try:
            self.login(user, data, req)
        except WrongPassword:
            self.logWarning(
                _("Could not login with account %(user)s | %(msg)s") % {"user": user
                                                                        , "msg": _("Wrong Password")})
            success = data['valid'] = False
        except Exception, e:
            self.logWarning(
                _("Could not login with account %(user)s | %(msg)s") % {"user": user
                                                                        , "msg": e})
            success = data['valid'] = False
            if self.core.debug:
                print_exc()
        else:
            success = True
        finally:
            if req:
                req.close()
            return success

    def relogin(self, user):
        req = self.getAccountRequest(user)
        if req:
            req.cj.clear()
            req.close()
        if user in self.infos:
            del self.infos[user] #delete old information

        return self._login(user, self.accounts[user])

    def setAccounts(self, accounts):
        self.accounts = accounts
        for user, data in self.accounts.iteritems():
            self._login(user, data)
            self.infos[user] = {}

    def updateAccounts(self, user, password=None, options={}):
        """ updates account and return true if anything changed """

        if user in self.accounts:
            self.accounts[user]['valid'] = True #do not remove or accounts will not login
            if password:
                self.accounts[user]['password'] = password
                self.relogin(user)
                return True
            if options:
                before = self.accounts[user]['options']
                self.accounts[user]['options'].update(options)
                return self.accounts[user]['options'] != before
        else:
            self.accounts[user] = {"password": password, "options": options, "valid": True}
            self._login(user, self.accounts[user])
            return True

    def removeAccount(self, user):
        if user in self.accounts:
            del self.accounts[user]
        if user in self.infos:
            del self.infos[user]
        if user in self.timestamps:
            del self.timestamps[user]

    @lock
    def getAccountInfo(self, name, force=False):
        """retrieve account infos for an user, do **not** overwrite this method!\\
        just use it to retrieve infos in hoster plugins. see `loadAccountInfo`

        :param name: username
        :param force: reloads cached account information
        :return: dictionary with information
        """
        data = Account.loadAccountInfo(self, name)

        if force or name not in self.infos:
            self.logDebug("Get Account Info for %s" % name)
            req = self.getAccountRequest(name)

            try:
                infos = self.loadAccountInfo(name, req)
                if not type(infos) == dict:
                    raise Exception("Wrong return format")
            except Exception, e:
                infos = {"error": str(e)}

            if req: req.close()

            self.logDebug("Account Info: %s" % str(infos))

            infos['timestamp'] = time()
            self.infos[name] = infos
        elif "timestamp" in self.infos[name] and self.infos[name][
                                                       "timestamp"] + self.info_threshold * 60 < time():
            self.logDebug("Reached timeout for account data")
            self.scheduleRefresh(name)

        data.update(self.infos[name])
        return data

    def isPremium(self, user):
        info = self.getAccountInfo(user)
        return info['premium']

    def loadAccountInfo(self, name, req=None):
        """this should be overwritten in account plugin,\
        and retrieving account information for user

        :param name:
        :param req: `Request` instance
        :return:
        """
        return {
            "validuntil": None, # -1 for unlimited
            "login": name,
            #"password": self.accounts[name]['password'], #@XXX: security
            "options": self.accounts[name]['options'],
            "valid": self.accounts[name]['valid'],
            "trafficleft": None, # in kb, -1 for unlimited
            "maxtraffic": None,
            "premium": True, #useful for free accounts
            "timestamp": 0, #time this info was retrieved
            "type": self.__name__,
            }

    def getAllAccounts(self, force=False):
        return [self.getAccountInfo(user, force) for user, data in self.accounts.iteritems()]

    def getAccountRequest(self, user=None):
        if not user:
            user, data = self.selectAccount()
        if not user:
            return None

        req = self.core.requestFactory.getRequest(self.__name__, user)
        return req

    def getAccountCookies(self, user=None):
        if not user:
            user, data = self.selectAccount()
        if not user:
            return None

        cj = self.core.requestFactory.getCookieJar(self.__name__, user)
        return cj

    def getAccountData(self, user):
        return self.accounts[user]

    def selectAccount(self):
        """ returns an valid account name and data"""
        usable = []
        for user, data in self.accounts.iteritems():
            if not data['valid']: continue

            if "time" in data['options'] and data['options']['time']:
                time_data = ""
                try:
                    time_data = data['options']['time'][0]
                    start, end = time_data.split("-")
                    if not compare_time(start.split(":"), end.split(":")):
                        continue
                except:
                    self.logWarning(_("Your Time %s has wrong format, use: 1:22-3:44") % time_data)

            if user in self.infos:
                if "validuntil" in self.infos[user]:
                    if self.infos[user]['validuntil'] > 0 and time() > self.infos[user]['validuntil']:
                        continue
                if "trafficleft" in self.infos[user]:
                    if self.infos[user]['trafficleft'] == 0:
                        continue

            usable.append((user, data))

        if not usable: return None, None
        return choice(usable)

    def canUse(self):
        return False if self.selectAccount() == (None, None) else True

    def parseTraffic(self, string): #returns kbyte
        return parseFileSize(string) / 1024

    def wrongPassword(self):
        raise WrongPassword

    def empty(self, user):
        if user in self.infos:
            self.logWarning(_("Account %s has not enough traffic, checking again in 30min") % user)

            self.infos[user].update({"trafficleft": 0})
            self.scheduleRefresh(user, 30 * 60)

    def expired(self, user):
        if user in self.infos:
            self.logWarning(_("Account %s is expired, checking again in 1h") % user)

            self.infos[user].update({"validuntil": time() - 1})
            self.scheduleRefresh(user, 60 * 60)

    def scheduleRefresh(self, user, time=0, force=True):
        """ add task to refresh account info to sheduler """
        self.logDebug("Scheduled Account refresh for %s in %s seconds." % (user, time))
        self.core.scheduler.addJob(time, self.getAccountInfo, [user, force])

    @lock
    def checkLogin(self, user):
        """ checks if user is still logged in """
        if user in self.timestamps:
            if self.login_timeout > 0 and self.timestamps[user] + self.login_timeout * 60 < time():
                self.logDebug("Reached login timeout for %s" % user)
                return self.relogin(user)
            else:
                return True
        else:
            return False
