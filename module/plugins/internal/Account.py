# -*- coding: utf-8 -*-

import random
import threading
import time
import traceback

from module.plugins.internal.Plugin import Plugin
from module.utils import compare_time, lock, parseFileSize


class WrongPassword(Exception):
    pass


class Account(Plugin):
    __name__    = "Account"
    __type__    = "account"
    __version__ = "0.04"

    __description__ = """Base account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


    def __init__(self, manager, accounts):
        super(Account, self).__init__(manager.core)

        self.manager = manager
        self.accounts = {}
        self.infos = {}  #: cache for account information
        self.lock = threading.RLock()
        self.timestamps = {}

        self.login_timeout  = 10 * 60  #: after that time (in minutes) pyload will relogin the account
        self.info_threshold = 10 * 60  #: after that time (in minutes) account data will be reloaded

        self.init()

        self.set_accounts(accounts)


    def init(self):
        pass


    def login(self, user, data, req):
        """
        Login into account, the cookies will be saved so user can be recognized

        :param user: loginname
        :param data: data dictionary
        :param req: `Request` instance
        """
        pass


    @lock
    def _login(self, user, data):
        #: set timestamp for login
        self.timestamps[user] = time.time()

        self.req = self.get_account_request(user)
        try:
            self.login(user, data, self.req)

        except WrongPassword:
            self.log_warning(
                _("Could not login with account %(user)s | %(msg)s") % {"user": user,
                                                                        "msg": _("Wrong Password")})
            success = data['valid'] = False

        except Exception, e:
            self.log_warning(
                _("Could not login with account %(user)s | %(msg)s") % {"user": user,
                                                                        "msg": e})
            success = data['valid'] = False
            if self.core.debug:
                traceback.print_exc()

        else:
            success = True

        finally:
            if hasattr(self, "req"):
                if self.req:
                    self.req.close()
                del self.req
            return success


    def relogin(self, user):
        req = self.get_account_request(user)
        if req:
            req.cj.clear()
            req.close()
        if user in self.infos:
            del self.infos[user]  #: delete old information

        return self._login(user, self.accounts[user])


    def set_accounts(self, accounts):
        self.accounts = accounts
        for user, data in self.accounts.iteritems():
            self._login(user, data)
            self.infos[user] = {}


    def update_accounts(self, user, password=None, options={}):
        """
        Updates account and return true if anything changed
        """
        if user in self.accounts:
            self.accounts[user]['valid'] = True  #: do not remove or accounts will not login
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


    #: Deprecated method, use `update_accounts` instead
    def updateAccounts(self, *args, **kwargs):
        return self.update_accounts(*args, **kwargs)


    def remove_account(self, user):
        if user in self.accounts:
            del self.accounts[user]
        if user in self.infos:
            del self.infos[user]
        if user in self.timestamps:
            del self.timestamps[user]


    #: Deprecated method, use `remove_account` instead
    def removeAccount(self, *args, **kwargs):
        return self.remove_account(*args, **kwargs)


    @lock
    def get_account_info(self, name, force=False):
        """
        Retrieve account infos for an user, do **not** overwrite this method!\\
        just use it to retrieve infos in hoster plugins. see `load_account_info`

        :param name: username
        :param force: reloads cached account information
        :return: dictionary with information
        """
        data = Account.load_account_info(self, name)

        if force or name not in self.infos:
            self.log_debug("Get Account Info for %s" % name)
            self.req  = self.get_account_request(name)

            try:
                infos = self.load_account_info(name, self.req)
                if not type(infos) == dict:
                    raise Exception("Wrong return format")

            except Exception, e:
                infos = super(self.__class__, self).load_account_info(name, self.req)
                infos['error'] = str(e)

                if self.core.debug:
                    traceback.print_exc()

            finally:
                if hasattr(self, "req"):
                    if self.req:
                        self.req.close()
                    del self.req

            self.log_debug("Account Info: %s" % infos)

            infos['timestamp'] = time.time()
            self.infos[name] = infos

        elif "timestamp" in self.infos[name] and self.infos[name]['timestamp'] + self.info_threshold * 60 < time.time():
            self.log_debug("Reached timeout for account data")
            self.schedule_refresh(name)

        data.update(self.infos[name])
        return data


    def is_premium(self, user):
        info = self.get_account_info(user)
        return info['premium']


    def load_account_info(self, name, req=None):
        """
        This should be overwritten in account plugin,\
        and retrieving account information for user

        :param name:
        :param req: `Request` instance
        :return:
        """
        return {"validuntil" : None,  #: -1 for unlimited
                "login"      : name,
                #: "password"   : self.accounts[name]['password'],  #: commented due security reason
                "options"    : self.accounts[name]['options'],
                "valid"      : self.accounts[name]['valid'],
                "trafficleft": None,  #: in bytes, -1 for unlimited
                "maxtraffic" : None,
                "premium"    : None,
                "timestamp"  : 0,  #: time this info was retrieved
                "type"       : self.__name__}


    def get_all_accounts(self, force=False):
        return [self.get_account_info(user, force) for user, data in self.accounts.iteritems()]


    #: Deprecated method, use `get_all_accounts` instead
    def getAllAccounts(self, *args, **kwargs):
        return self.get_all_accounts(*args, **kwargs)


    def get_account_request(self, user=None):
        if not user:
            user, data = self.select_account()

        return self.core.requestFactory.getRequest(self.__name__, user)


    def get_account_cookies(self, user=None):
        if not user:
            user, data = self.select_account()
        if not user:
            return None

        cj = self.core.requestFactory.getCookieJar(self.__name__, user)
        return cj


    def get_account_data(self, user):
        return self.accounts[user]


    def select_account(self):
        """
        Returns an valid account name and data
        """
        usable = []
        for user, data in self.accounts.iteritems():
            if not data['valid']:
                continue

            if "time" in data['options'] and data['options']['time']:
                time_data = ""
                try:
                    time_data = data['options']['time'][0]
                    start, end = time_data.split("-")
                    if not compare_time(start.split(":"), end.split(":")):
                        continue
                except Exception:
                    self.log_warning(_("Your Time %s has wrong format, use: 1:22-3:44") % time_data)

            if user in self.infos:
                if "validuntil" in self.infos[user]:
                    if self.infos[user]['validuntil'] > 0 and time.time() > self.infos[user]['validuntil']:
                        continue
                if "trafficleft" in self.infos[user]:
                    if self.infos[user]['trafficleft'] == 0:
                        continue

            usable.append((user, data))

        if not usable:
            return None, None

        return random.choice(usable)


    def can_use(self):
        return self.select_account() != (None, None)


    def parse_traffic(self, value, unit=None):  #: return kilobytes
        if not unit and not isinstance(value, basestring):
            unit = "KB"
        return parseFileSize(value, unit)


    def wrong_password(self):
        raise WrongPassword


    def empty(self, user):
        if user in self.infos:
            self.log_warning(_("Account %s has not enough traffic, checking again in 30min") % user)

            self.infos[user].update({"trafficleft": 0})
            self.schedule_refresh(user, 30 * 60)


    def expired(self, user):
        if user in self.infos:
            self.log_warning(_("Account %s is expired, checking again in 1h") % user)

            self.infos[user].update({"validuntil": time.time() - 1})
            self.schedule_refresh(user, 60 * 60)


    def schedule_refresh(self, user, time=0, force=True):
        """
        Add task to refresh account info to sheduler
        """
        self.log_debug("Scheduled Account refresh for %s in %s seconds." % (user, time))
        self.core.scheduler.addJob(time, self.get_account_info, [user, force])


    #: Deprecated method, use `schedule_refresh` instead
    def scheduleRefresh(self, *args, **kwargs):
        return self.schedule_refresh(*args, **kwargs)


    @lock
    def check_login(self, user):
        """
        Checks if user is still logged in
        """
        if user in self.timestamps:
            if self.login_timeout > 0 and self.timestamps[user] + self.login_timeout * 60 < time.time():
                self.log_debug("Reached login timeout for %s" % user)
                return self.relogin(user)
            else:
                return True
        else:
            return False
