# -*- coding: utf-8 -*-

from __future__ import with_statement

import random
import time
import threading
import traceback

from module.plugins.internal.Plugin import Plugin
from module.utils import compare_time, lock, parseFileSize as parse_size


class Account(Plugin):
    __name__    = "Account"
    __type__    = "account"
    __version__ = "0.06"
    __status__  = "testing"

    __description__ = """Base account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LOGIN_TIMEOUT  = 10 * 60  #: After that time (in minutes) pyload will relogin the account
    INFO_THRESHOLD = 10 * 60  #: After that time (in minutes) account data will be reloaded


    def __init__(self, manager, accounts):
        self.pyload = manager.core
        self.info   = {}  #: Provide information in dict here
        self.lock   = threading.RLock()

        self.init()
        self.init_accounts(accounts)


    def init(self):
        """
        Initialize additional data structures
        """
        pass


    def login(self, user, password, data, req):
        """
        Login into account, the cookies will be saved so user can be recognized
        """
        pass


    @lock
    def _login(self, user):
        try:
            info = self.info[user]
            info['login']['timestamp'] = time.time()  #: Set timestamp for login

            self.req = self.get_request(user)
            self.login(user, info['login']['password'], info['data'], self.req)

        except Exception, e:
            self.log_warning(_("Could not login with username ") + user, e)
            res = info['login']['valid'] = False
            if self.pyload.debug:
                traceback.print_exc()

        else:
            res = info['login']['valid'] = True

        finally:
            if self.req:
                self.req.close()
            del self.req

            return res


    def relogin(self, user):
        with self.get_request(user) as req:
            req.clearCookies()

        if user in self.info:
            self.info[user]['login'].clear()

        return self._login(user)


    #@TODO: Rewrite in 0.4.10
    def init_accounts(self, accounts):
        for user, data in accounts.items():
            self.add(user, data['password'], data['options'])
            self._login(user)


    @lock
    def add(self, user, password=None, options={}):
        if user not in self.info:
            self.info[user] = {'login': {'valid': None, 'password': password or "", 'timestamp': 0},
                               'data' : {'options': options, 'timestamp': 0}}
            self._login(user)
            return True
        else:
            self.log_error(_("Error adding account"), _("User already exists"))


    @lock
    def update(self, user, password=None, options={}):
        """
        Updates account and return true if anything changed
        """
        if user not in self.info:
            return self.add(user, password, options)

        elif password or options:
            if password:
                self.info[user]['login']['password'] = password
                self.relogin(user)
                return True

            if options:
                before = self.info[user]['data'][user]['options']
                self.info[user]['data']['options'].update(options)
                return self.info[user]['data']['options'] != before


    #: Deprecated method, use `update` instead (Remove in 0.4.10)
    def updateAccounts(self, *args, **kwargs):
        return self.update(*args, **kwargs)


    def remove(self, user=None): # -> def remove
        if not user:
            self.info.clear()

        elif user in self.info:
            self.info.pop(user, None)


    #: Deprecated method, use `remove` instead (Remove in 0.4.10)
    def removeAccount(self, *args, **kwargs):
        return self.remove(*args, **kwargs)


    def get_data(self, user, reload=False):
        if not user:
            return

        info = self.get_info(user, reload)
        if info and 'data' in info:
            return info['data']


    #: Deprecated method, use `get_data` instead (Remove in 0.4.10)
    def getAccountData(self, *args, **kwargs):
        if 'force' in kwargs:
            kwargs['reload'] = kwargs['force']
            kwargs.pop('force', None)
        data = self.get_data(*args, **kwargs) or {}
        if 'options' not in data:
            data['options'] = {'limitdl': ['0']}
        return data

    @lock
    def get_info(self, user, reload=False):
        """
        Retrieve account infos for an user, do **not** overwrite this method!\\
        just use it to retrieve infos in hoster plugins. see `parse_info`

        :param user: username
        :param reload: reloads cached account information
        :return: dictionary with information
        """
        if user not in self.info:
            self.log_error(_("User %s not found while retrieving account info") % user)
            return

        elif reload:
            self.log_debug("Get Account Info for: %s" % user)
            info = self._parse_info(user)

        else:
            info = self.info[user]

            if self.INFO_THRESHOLD > 0 and info['data']['timestamp'] + self.INFO_THRESHOLD * 60 < time.time():
                self.log_debug("Reached data timeout for %s" % user)
                self.schedule_refresh(user)

        safe_info = info.copy()
        safe_info['login']['password'] = "**********"
        self.log_debug("Account info: %s" % safe_info)
        return info


    def is_premium(self, user):
        if not user:
            return False

        info = self.get_info(user, reload)
        return info['premium'] if info and 'premium' in info else False


    def _parse_info(self, user):
        info = self.info[user]
        data = info['data']

        #@TODO: Remove in 0.4.10
        data.update({'login': user,
                     'type' : self.__name__,
                     'valid': self.info[user]['login']['valid']})

        try:
            data['timestamp'] = time.time()  #: Set timestamp for login

            self.req   = self.get_request(user)
            extra_info = self.parse_info(user, info['login']['password'], info, self.req)

            if extra_info and isinstance(extra_info, dict):
                data.update(extra_info)

        except Exception, e:
            self.log_warning(_("Error loading info for ") + user, e)

            if self.pyload.debug:
                traceback.print_exc()

        else:
            for key in ('premium', 'validuntil', 'trafficleft', 'maxtraffic'):
                if key not in data:
                    data[key] = None

        finally:
            if self.req:
                self.req.close()
            del self.req

            self.info[user].update(info)
            return info


    def parse_info(self, user, password, info, req):
        """
        This should be overwritten in account plugin
        and retrieving account information for user

        :param user:
        :param req: `Request` instance
        :return:
        """
        pass


    #: Remove in 0.4.10
    def getAllAccounts(self, *args, **kwargs):
        return [self.getAccountData(user, *args, **kwargs) for user, info in self.info.items()]


    def login_fail(self, reason=_("Login handshake has failed")):
        return self.fail(reason)


    def get_request(self, user=None):
        if not user:
            user, info = self.select()

        return self.pyload.requestFactory.getRequest(self.__name__, user)


    def get_cookies(self, user=None):
        if not user:
            user, info = self.select()

        return self.pyload.requestFactory.getCookieJar(self.__name__, user)


    #@TODO: Random account only? Simply crazy... rewrite
    def select(self):
        """
        Returns an valid account name and data
        """
        usable = []
        for user, info in self.info.items():
            if not info['login']['valid']:
                continue

            options = info['data']['options']
            if "time" in options and options['time']:
                time_data = ""
                try:
                    time_data = options['time'][0]
                    start, end = time_data.split("-")
                    if not compare_time(start.split(":"), end.split(":")):
                        continue

                except Exception:
                    self.log_warning(_("Your time %s has wrong format, use 1:22-3:44") % time_data)

            if user in self.info:
                if None is not self.info[user]['validuntil'] > 0 and time.time() > self.info[user]['validuntil']:
                    continue
                if None is not self.info[user]['trafficleft'] == 0:
                    continue

            usable.append((user, info))

        if not usable:
            return None, None

        return random.choice(usable)


    def can_use(self):
        return self.select() != (None, None)


    def parse_traffic(self, value, unit=None):  #: Return kilobytes
        if not unit and not isinstance(value, basestring):
            unit = "KB"

        return parse_size(value, unit)


    def empty(self, user):
        if user not in self.info:
            return

        self.log_warning(_("Account %s has not enough traffic, checking again in 30min") % user)

        self.info[user]['data'].update({'trafficleft': 0})
        self.schedule_refresh(user, 30 * 60)


    def expired(self, user):
        if user not in self.info:
            return

        self.log_warning(_("Account %s is expired, checking again in 1h") % user)

        self.info[user]['data'].update({'validuntil': time.time() - 1})
        self.schedule_refresh(user, 60 * 60)


    def schedule_refresh(self, user, time=0, reload=True):
        """
        Add task to refresh account info to sheduler
        """
        self.log_debug("Scheduled refresh for %s in %s seconds" % (user, time))
        self.pyload.scheduler.addJob(time, self.get_info, [user, reload])


    #: Deprecated method, use `schedule_refresh` instead (Remove in 0.4.10)
    def scheduleRefresh(self, *args, **kwargs):
        if 'force' in kwargs:
            kwargs['reload'] = kwargs['force']
            kwargs.pop('force', None)
        return self.schedule_refresh(*args, **kwargs)


    @lock
    def is_logged(self, user):
        """
        Checks if user is still logged in
        """
        if user in self.info:
            if self.LOGIN_TIMEOUT > 0 and self.info[user]['login']['timestamp'] + self.LOGIN_TIMEOUT * 60 < time.time():
                self.log_debug("Reached login timeout for %s" % user)
                return self.relogin(user)
            else:
                return True
        else:
            return False
