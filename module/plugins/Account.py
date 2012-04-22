# -*- coding: utf-8 -*-

from time import time
from traceback import print_exc
from threading import RLock

from module.utils import compare_time, format_size, parseFileSize, lock, from_string
from module.Api import AccountInfo
from module.network.CookieJar import CookieJar

from Base import Base

class WrongPassword(Exception):
    pass

#noinspection PyUnresolvedReferences
class Account(Base, AccountInfo):
    """
    Base class for every account plugin.
    Just overwrite `login` and cookies will be stored and the account becomes accessible in\
    associated hoster plugin. Plugin should also provide `loadAccountInfo`. \
    An instance of this class is created for every entered account, it holds all \
    fields of AccountInfo ttype, and can be set easily at runtime.
    """

    # constants for special values
    UNKNOWN = -1
    UNLIMITED = -2

    # Default values
    valid = True
    validuntil = -1
    trafficleft = -1
    maxtraffic = -1
    premium = True
    activated = True

    #: after that time [in minutes] pyload will relogin the account
    login_timeout = 600
    #: account data will be reloaded after this time
    info_threshold = 600

    # known options
    known_opt = ("time", "limitDL")

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

    def login(self, req):
        """login into account, the cookies will be saved so the user can be recognized

        :param req: `Request` instance
        """
        raise NotImplemented

    def relogin(self):
        """ Force a login. """
        req = self.getAccountRequest()
        try:
            return self._login(req)
        finally:
            req.close()

    @lock
    def _login(self, req):
        # set timestamp for login
        self.login_ts = time()

        try:
            try:
                self.login(req)
            except TypeError: #TODO: temporary
                self.logDebug("Deprecated .login(...) signature omit user, data")
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

        return self.valid

    def restoreDefaults(self):
        self.validuntil = Account.validuntil
        self.trafficleft = Account.trafficleft
        self.maxtraffic = Account.maxtraffic
        self.premium = Account.premium

    def update(self, password=None, options=None):
        """ updates the account and returns true if anything changed """

        self.login_ts = 0
        self.valid = True #set valid, so the login will be retried

        if "activated" in options:
            self.activated = from_string(options["avtivated"], "bool")

        if password:
            self.password = password
            self.relogin()
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

    def getDownloadSettings(self):
        """ Can be overwritten to change download settings. Default is no chunkLimit, max dl limit, resumeDownload

        :return: (chunkLimit, limitDL, resumeDownload) / (int, int ,bool)
        """
        return -1, 0, True

    @lock
    def getAccountInfo(self, force=False):
        """retrieve account info's for an user, do **not** overwrite this method!\\
        just use it to retrieve info's in hoster plugins. see `loadAccountInfo`

        :param name: username
        :param force: reloads cached account information
        :return: dictionary with information
        """
        if force or self.timestamp + self.info_threshold * 60 < time():

            # make sure to login
            req = self.getAccountRequest()
            self.checkLogin(req)
            self.logDebug("Get Account Info for %s" % self.loginname)
            try:
                try:
                    infos = self.loadAccountInfo(req)
                except TypeError: #TODO: temporary
                    self.logDebug("Deprecated .loadAccountInfo(...) signature, omit user argument.")
                    infos = self.loadAccountInfo(self.loginname, req)
            except Exception, e:
                infos = {"error": str(e)}
            finally:
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
    def loadAccountInfo(self, req):
        """ Overwrite this method and set account attributes within this method.

        :param user: Deprecated
        :param req: Request instance
        :return:
        """
        pass

    def getAccountCookies(self, user):
        self.logDebug("Deprecated method .getAccountCookies -> use account.cj")
        return self.cj

    def getAccountData(self, user):
        self.logDebug("Deprecated method .getAccountData -> use fields directly")
        return {"password": self.password}

    def isPremium(self, user=None):
        if user: self.logDebug("Deprecated Argument user for .isPremium()", user)
        return self.premium

    def isUsable(self):
        """Check several constraints to determine if account should be used"""
        if not self.valid or not self.activated: return False

        if self.options["time"]:
            time_data = ""
            try:
                time_data = self.options["time"]
                start, end = time_data.split("-")
                if not compare_time(start.split(":"), end.split(":")):
                    return False
            except:
                self.logWarning(_("Your Time %s has a wrong format, use: 1:22-3:44") % time_data)

        if 0 <= self.validuntil < time():
            return False
        if self.trafficleft is 0:  # test explicitly for 0
            return False

        return True

    def parseTraffic(self, string): #returns kbyte
        return parseFileSize(string) / 1024

    def formatTrafficleft(self):
        if self.trafficleft is None:
            self.getAccountInfo(force=True)
        return format_size(self.trafficleft*1024)

    def wrongPassword(self):
        raise WrongPassword

    def empty(self, user=None):
        if user: self.logDebug("Deprecated argument user for .empty()", user)

        self.logWarning(_("Account %s has not enough traffic, checking again in 30min") % self.login)

        self.trafficleft = 0
        self.scheduleRefresh(30 * 60)

    def expired(self, user=None):
        if user: self.logDebug("Deprecated argument user for .expired()", user)

        self.logWarning(_("Account %s is expired, checking again in 1h") % user)

        self.validuntil = time() - 1
        self.scheduleRefresh(60 * 60)

    def scheduleRefresh(self, time=0, force=True):
        """ add a task for refreshing the account info to the scheduler """
        self.logDebug("Scheduled Account refresh for %s in %s seconds." % (self.loginname, time))
        self.core.scheduler.addJob(time, self.getAccountInfo, [force])

    @lock
    def checkLogin(self, req):
        """ checks if the user is still logged in """
        if self.login_ts + self.login_timeout * 60 < time():
            if self.login_ts: # separate from fresh login to have better debug logs
                self.logDebug("Reached login timeout for %s" % self.loginname)
            else:
                self.logDebug("Login with %s" % self.loginname)

            self._login(req)
            return False

        return True
