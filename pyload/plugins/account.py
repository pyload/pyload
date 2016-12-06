# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
from builtins import str
from past.utils import old_div
from time import time
from threading import RLock

from pyload.Api import AccountInfo, ConfigItem
from pyload.network.CookieJar import CookieJar
from pyload.config.convert import from_string, to_configdata
from pyload.utils import to_string, compare_time, format_size, parseFileSize, lock

from .Base import Base


class WrongPassword(Exception):
    pass


#noinspection PyUnresolvedReferences
class Account(Base):
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

    #: after that time [in minutes] pyload will relogin the account
    login_timeout = 600
    #: account data will be reloaded after this time
    info_threshold = 600

    @classmethod
    def fromInfoData(cls, m, info, password, options):
        return cls(m, info.aid, info.loginname, info.owner,
                   True if info.activated else False, True if info.shared else False, password, options)

    __type__ = "account"

    def __init__(self, manager, aid, loginname, owner, activated, shared, password, options):
        Base.__init__(self, manager.core, owner)

        self.aid = aid
        self.loginname = loginname
        self.owner = owner
        self.activated = activated
        self.shared = shared
        self.password = password
        self.options = options

        self.manager = manager

        self.lock = RLock()
        self.timestamp = 0
        self.login_ts = 0 # timestamp for login
        self.cj = CookieJar()
        self.error = None

        try:
            self.config_data = dict(to_configdata(x) for x in self.__config__)
        except Exception as e:
            self.logError("Invalid config: %s" % e)
            self.config_data = {}

        self.init()

    def toInfoData(self):
        info = AccountInfo(self.aid, self.__name__, self.loginname, self.owner, self.valid, self.validuntil, self.trafficleft,
                           self.maxtraffic, self.premium, self.activated, self.shared, self.options)

        info.config = [ConfigItem(name, item.label, item.description, item.input,
                                  to_string(self.getConfig(name))) for name, item in
                       self.config_data.items()]
        return info

    def init(self):
        pass

    def getConfig(self, option):
        """ Gets an option that was configured via the account options dialog and
        is only valid for this specific instance."""
        if option not in self.config_data:
            return Base.getConfig(self, option)

        if option in self.options:
            return self.options[option]

        return self.config_data[option].input.default_value

    def setConfig(self, option, value):
        """ Sets a config value for this account instance. Modifying the global values is not allowed. """
        if option not in self.config_data:
            return

        value = from_string(value, self.config_data[option].input.type)
        # given value is the default value and does not need to be saved at all
        if value == self.config_data[option].input.default_value:
            if option in self.options:
                del self.options[option]
        else:
            self.options[option] = from_string(value, self.config_data[option].input.type)

    def login(self, req):
        """login into account, the cookies will be saved so the user can be recognized

        :param req: `Request` instance
        """
        raise NotImplementedError

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

        except Exception as e:
            self.logWarning(
                _("Could not login with account %(user)s | %(msg)s") % {"user": self.loginname
                    , "msg": e})
            self.valid = False
            self.core.print_exc()

        return self.valid

    def restoreDefaults(self):
        self.validuntil = Account.validuntil
        self.trafficleft = Account.trafficleft
        self.maxtraffic = Account.maxtraffic
        self.premium = Account.premium

    def setLogin(self, loginname, password):
        """ updates the loginname and password and returns true if anything changed """

        if password != self.password or loginname != self.loginname:
            self.login_ts = 0
            self.valid = True #set valid, so the login will be retried

            self.loginname = loginname
            self.password = password
            return True

        return False

    def updateConfig(self, items):
        """  Updates the accounts options from config items """
        for item in items:
            # Check if a valid option
            if item.name in self.config_data:
                self.setConfig(item.name, item.value)

    def getAccountRequest(self):
        return self.core.requestFactory.getRequest(self.cj)

    def getDownloadSettings(self):
        """ Can be overwritten to change download settings. Default is no chunkLimit, max dl limit, resumeDownload

        :return: (chunkLimit, limitDL, resumeDownload) / (int, int, bool)
        """
        return -1, 0, True

    # TODO: this method is ambiguous, it returns nothing, but just retrieves the data if needed
    @lock
    def getAccountInfo(self, force=False):
        """retrieve account info's for an user, do **not** overwrite this method!\\
        just use it to retrieve info's in hoster plugins. see `loadAccountInfo`

        :param name: username
        :param force: reloads cached account information
        """
        if force or self.timestamp + self.info_threshold * 60 < time():

            # make sure to login
            req = self.getAccountRequest()
            self.checkLogin(req)
            self.logInfo(_("Get Account Info for %s") % self.loginname)
            try:
                try:
                    infos = self.loadAccountInfo(req)
                except TypeError: #TODO: temporary
                    self.logDebug("Deprecated .loadAccountInfo(...) signature, omit user argument.")
                    infos = self.loadAccountInfo(self.loginname, req)
            except Exception as e:
                infos = {"error": str(e)}
                self.logError(_("Error: %s") % e)
            finally:
                req.close()

            self.restoreDefaults() # reset to initial state
            if isinstance(infos, dict): # copy result from dict to class
                for k, v in infos.items():
                    if hasattr(self, k):
                        setattr(self, k, v)
                    else:
                        self.logDebug("Unknown attribute %s=%s" % (k, v))

            self.logDebug("Account Info: %s" % str(infos))
            self.timestamp = time()
            self.core.evm.dispatchEvent("account:loaded", self.toInfoData())

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

    def selectAccount(self, *args):
        self.logDebug("Deprecated method .selectAccount() -> use fields directly")
        return self.loginname, self.getAccountData()

    def getAccountData(self, *args):
        self.logDebug("Deprecated method .getAccountData -> use fields directly")
        return {"password": self.password, "premium": self.premium, "trafficleft": self.trafficleft,
                "maxtraffic" : self.maxtraffic, "validuntil": self.validuntil}

    def isPremium(self, user=None):
        if user: self.logDebug("Deprecated Argument user for .isPremium()", user)
        return self.premium

    def isUsable(self):
        """Check several constraints to determine if account should be used"""

        if not self.valid or not self.activated: return False

        # TODO: not in ui currently
        if "time" in self.options and self.options["time"]:
            time_data = ""
            try:
                time_data = self.options["time"]
                start, end = time_data.split("-")
                if not compare_time(start.split(":"), end.split(":")):
                    return False
            except Exception:
                self.logWarning(_("Your Time %s has a wrong format, use: 1:22-3:44") % time_data)

        if 0 <= self.validuntil < time():
            return False
        if self.trafficleft is 0:  # test explicitly for 0
            return False

        return True

    def parseTraffic(self, string): #returns kbyte
        return old_div(parseFileSize(string), 1024)

    def formatTrafficleft(self):
        if self.trafficleft is None:
            self.getAccountInfo(force=True)
        return format_size(self.trafficleft * 1024)

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
                self.logInfo(_("Login with %s") % self.loginname)

            self._login(req)
            return False

        return True
