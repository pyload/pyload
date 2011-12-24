# -*- coding: utf-8 -*-

from time import time
from traceback import print_exc
from threading import RLock

from Plugin import Base
from module.utils import compare_time, parseFileSize, lock
from module.config.converter import from_string
from module.Api import AccountInfo
from module.network.CookieJar import CookieJar

class WrongPassword(Exception):
    pass

#noinspection PyUnresolvedReferences
class Account(Base, AccountInfo):
    """
    Base class for every Account plugin.
    Just overwrite `login` and cookies will be stored and account becomes accessible in\
    associated hoster plugin. Plugin should also provide `loadAccountInfo`
    """

    # Default values
    valid = True
    validuntil = None
    trafficleft = None
    maxtraffic = None
    premium = True
    activated = True

    #: after that time [in minutes] pyload will relogin the account
    login_timeout = 600
    #: account data will be reloaded after this time
    info_threshold = 600

    # known options
    known_opt = ["time", "limitDL"]


    def __init__(self, manager, loginname, password, options):
        Base.__init__(self, manager.core)

        if "activated" in options:
            activated = from_string(options["activated"], "bool")
        else:
            activated = Account.activated

        for opt in self.known_opt:
            if opt not in options:
                options[opt] = ""

        for opt in options.keys():
            if opt not in self.known_opt:
                del options[opt]

        # default account attributes
        AccountInfo.__init__(self, self.__name__, loginname, Account.valid, Account.validuntil, Account.trafficleft,
            Account.maxtraffic, Account.premium, activated, options)

        self.manager = manager

        self.lock = RLock()
        self.timestamp = 0
        self.login_ts = 0 # timestamp for login
        self.cj = CookieJar(self.__name__)
        self.password = password
        self.error = None

        self.init()

    def init(self):
        pass

    #TODO: remove user, data
    def login(self, user, data, req):
        """login into account, the cookies will be saved so user can be recognized

        :param user: Deprecated
        :param data: Deprecated
        :param req: `Request` instance
        """
        raise NotImplemented

    def relogin(self):
        """ Force a login, same as `_login` """
        return self._login()

    @lock
    def _login(self):
        # set timestamp for login
        self.login_ts = time()

        req = self.getAccountRequest()
        try:
            self.login(self.loginname, {"password": self.password}, req)
            self.valid = True
        except WrongPassword:
            self.logWarning(
                _("Could not login with account %(user)s | %(msg)s") % {"user": self.loginname
                    , "msg": _("Wrong Password")})
            self.valid = False

        except Exception, e:
            self.logWarning(
                _("Could not login with account %(user)s | %(msg)s") % {"user": self.loginname
                    , "msg": e})
            self.valid = False
            if self.core.debug:
                print_exc()
        finally:
            req.close()

        return self.valid

    def restoreDefaults(self):
        self.valid = Account.valid
        self.validuntil = Account.validuntil
        self.trafficleft = Account.trafficleft
        self.maxtraffic = Account.maxtraffic
        self.premium = Account.premium
        self.activated = Account.activated

    def update(self, password=None, options={}):
        """ updates account and return true if anything changed """

        self.login_ts = 0

        if "activated" in options:
            self.activated = from_string(options["avtivated"], "bool")

        if password:
            self.password = password
            self._login()
            return True
        if options:
            # remove unknown options
            for opt in options.keys():
                if opt not in self.known_opt:
                    del options[opt]

            before = self.options
            self.options.update(options)
            return self.options != before

    def getAccountRequest(self):
        return self.core.requestFactory.getRequest(self.__name__, self.cj)

    @lock
    def getAccountInfo(self, force=False):
        """retrieve account infos for an user, do **not** overwrite this method!\\
        just use it to retrieve infos in hoster plugins. see `loadAccountInfo`

        :param name: username
        :param force: reloads cached account information
        :return: dictionary with information
        """
        if force or self.timestamp + self.info_threshold * 60 < time():

            # make sure to login
            self.checkLogin()
            self.logDebug("Get Account Info for %s" % self.loginname)
            req = self.getAccountRequest()

            try:
                infos = self.loadAccountInfo(self.loginname, req)
            except Exception, e:
                infos = {"error": str(e)}

            req.close()

            self.logDebug("Account Info: %s" % str(infos))
            self.timestamp = time()

            self.restoreDefaults() # reset to initial state
            if type(infos) == dict: # copy result from dict to class
                for k, v in infos.iteritems():
                    if hasattr(self, k):
                        setattr(self, k, v)
                    else:
                        self.logDebug("Unknown attribute %s=%s" % (k, v))

    #TODO: remove user
    def loadAccountInfo(self, user, req):
        """ Overwrite this method and set account attributes within this method.

        :param user: Deprecated
        :param req: Request instance
        :return:
        """
        pass

    def isPremium(self, user=None):
        if user: self.logDebug("Deprecated Argument user for .isPremium()", user)
        return self.premium

    def isUsable(self):
        """Check several contraints to determine if account should be used"""
        if not self.valid or not self.activated: return False

        if self.options["time"]:
            time_data = ""
            try:
                time_data = self.options["time"]
                start, end = time_data.split("-")
                if not compare_time(start.split(":"), end.split(":")):
                    return False
            except:
                self.logWarning(_("Your Time %s has wrong format, use: 1:22-3:44") % time_data)

        if 0 < self.validuntil < time():
            return False
        if self.trafficleft is 0:  # test explicity for 0
            return False

        return True

    def parseTraffic(self, string): #returns kbyte
        return parseFileSize(string) / 1024

    def wrongPassword(self):
        raise WrongPassword

    def empty(self, user=None):
        if user: self.logDebug("Deprecated argument user for .empty()", user)

        self.logWarning(_("Account %s has not enough traffic, checking again in 30min") % self.login)

        self.trafficleft = 0
        self.scheduleRefresh(30 * 60)

    def expired(self, user):
        if user in self.infos:
            self.logWarning(_("Account %s is expired, checking again in 1h") % user)

            self.validuntil = time() - 1
            self.scheduleRefresh(60 * 60)

    def scheduleRefresh(self, time=0, force=True):
        """ add task to refresh account info to sheduler """
        self.logDebug("Scheduled Account refresh for %s in %s seconds." % (self.loginname, time))
        self.core.scheduler.addJob(time, self.getAccountInfo, [force])

    @lock
    def checkLogin(self):
        """ checks if user is still logged in """
        if self.login_ts + self.login_timeout * 60 < time():
            if self.login_ts: # seperate from fresh login to have better debug logs
                self.logDebug("Reached login timeout for %s" % self.loginname)
            else:
                self.logDebug("Login with %s" % self.loginname)

            self._login()
            return False

        return True
