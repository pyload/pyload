# -*- coding: utf-8 -*-

import copy
import random
import time
import threading
import traceback

from module.plugins.internal.Plugin import Plugin
from module.utils import compare_time, lock, parseFileSize as parse_size


class Account(Plugin):
    __name__    = "Account"
    __type__    = "account"
    __version__ = "0.15"
    __status__  = "testing"

    __description__ = """Base account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    LOGIN_TIMEOUT  = 10 * 60  #: After that time (in minutes) pyload will relogin the account
    INFO_THRESHOLD = 30 * 60  #: After that time (in minutes) account data will be reloaded


    def __init__(self, manager, accounts):
        self._init(manager.core)

        self.lock     = threading.RLock()
        self.accounts = accounts  #@TODO: Remove in 0.4.10

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
            self.log_warning(_("Could not login user `%s`") % user, e)
            res = info['login']['valid'] = False
            self.accounts[user]['valid'] = False  #@TODO: Remove in 0.4.10

            if self.pyload.debug:
                traceback.print_exc()

        else:
            res = info['login']['valid'] = True
            self.accounts[user]['valid'] = True  #@TODO: Remove in 0.4.10

        finally:
            self.clean()
            return res


    def relogin(self, user):
        self.log_info(_("Relogin user `%s`...") % user)

        req = self.get_request(user)
        if req:
            req.clearCookies()
            self.clean()

        if user in self.info:
            self.info[user]['login'].clear()

        return self._login(user)


    #@TODO: Rewrite in 0.4.10
    def init_accounts(self, accounts):
        for user, data in accounts.items():
            self.add(user, data['password'], data['options'])


    @lock
    def add(self, user, password=None, options={}):
        if user not in self.info:
            self.info[user] = {'login': {'valid'    : None,
                                         'password' : password or "",
                                         'timestamp': 0},
                               'data' : {'options'    : options,
                                         'premium'    : None,
                                         'validuntil' : None,
                                         'trafficleft': None,
                                         'maxtraffic' : None}}

            #@TODO: Remove in 0.4.10
            self.accounts[user] = self.info[user]['data']
            self.accounts[user].update({'login'   : user,
                                        'type'    : self.__name__,
                                        'valid'   : self.info[user]['login']['valid'],
                                        'password': self.info[user]['login']['password']})

            self.log_info(_("Login user `%s`...") % user)
            self._login(user)
            return True

        else:
            self.log_error(_("Error adding user `%s`") % user, _("User already exists"))


    @lock
    def update(self, user, password=None, options={}):
        """
        Updates account and return true if anything changed
        """
        if not (password or options):
            return

        if user not in self.info:
            return self.add(user, password, options)

        else:
            if password:
                self.info[user]['login']['password'] = password
                self.accounts[user]['password']      = password  #@TODO: Remove in 0.4.10
                self.relogin(user)

            if options:
                before = self.info[user]['data']['options']
                self.info[user]['data']['options'].update(options)
                return self.info[user]['data']['options'] != before

            return True


    #: Deprecated method, use `update` instead (Remove in 0.4.10)
    def updateAccounts(self, *args, **kwargs):
        return self.update(*args, **kwargs)


    def remove(self, user=None): # -> def remove
        if not user:
            self.info.clear()
            self.accounts.clear()  #@TODO: Remove in 0.4.10

        elif user in self.info:
            self.info.pop(user, None)
            self.accounts.pop(user, None)  #@TODO: Remove in 0.4.10


    #: Deprecated method, use `remove` instead (Remove in 0.4.10)
    def removeAccount(self, *args, **kwargs):
        return self.remove(*args, **kwargs)


    #@NOTE: Remove in 0.4.10?
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
            self.log_error(_("User `%s` not found while retrieving account info") % user)
            return

        elif reload:
            self.log_info(_("Parsing account info for user `%s`...") % user)
            info = self._parse_info(user)

            safe_info = copy.deepcopy(info)
            safe_info['login']['password'] = "**********"
            safe_info['data']['password']  = "**********"  #@TODO: Remove in 0.4.10
            self.log_debug("Account info for user `%s`: %s" % (user, safe_info))

        else:
            info = self.info[user]

            if self.INFO_THRESHOLD > 0 and info['login']['timestamp'] + self.INFO_THRESHOLD < time.time():
                self.log_debug("Reached data timeout for %s" % user)
                self.schedule_refresh(user)

        return info


    def is_premium(self, user):
        if not user:
            return False

        info = self.get_info(user)
        return info['data']['premium']


    def _parse_info(self, user):
        info = self.info[user]

        if not info['login']['valid']:
            return info

        try:
            self.req   = self.get_request(user)
            extra_info = self.parse_info(user, info['login']['password'], info, self.req)

            if extra_info and isinstance(extra_info, dict):
                info['data'].update(extra_info)

        except (Fail, Exception), e:
            self.log_warning(_("Error loading info for user `%s`") % user, e)

            if self.pyload.debug:
                traceback.print_exc()

        finally:
            self.clean()

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


    def select(self):
        """
        Returns a valid account name and info
        """
        free_accounts    = {}
        premium_accounts = {}

        for user, info in self.info.items():
            if not info['login']['valid']:
                continue

            data = info['data']

            if "time" in data['options'] and data['options']['time']:
                time_data = ""
                try:
                    time_data  = data['options']['time'][0]
                    start, end = time_data.split("-")

                    if not compare_time(start.split(":"), end.split(":")):
                        continue

                except Exception:
                    self.log_warning(_("Wrong time format `%s` for account `%s`, use 1:22-3:44") % (user, time_data))

            if data['trafficleft'] == 0:
                continue

            if time.time() > data['validuntil'] > 0:
                continue

            if data['premium']:
                premium_accounts[user] = info

            else:
                free_accounts[user] = info

        account_list = (premium_accounts or free_accounts).items()

        if not account_list:
            return None, None

        validuntil_list = [(user, info) for user, info in account_list if info['data']['validuntil']]

        if not validuntil_list:
            return random.choice(account_list)  #@TODO: Random account?! Recheck in 0.4.10

        return sorted(validuntil_list,
                      key=lambda a: a[1]['data']['validuntil'],
                      reverse=True)[0]


    def parse_traffic(self, value, unit=None):  #: Return kilobytes
        if not unit and not isinstance(value, basestring):
            unit = "KB"

        return parse_size(value, unit)


    def empty(self, user):
        if user not in self.info:
            return

        self.log_warning(_("Account `%s` has not enough traffic") % user, _("Checking again in 30 minutes"))

        self.info[user]['data']['trafficleft'] = 0
        self.schedule_refresh(user, 30 * 60)


    def expired(self, user):
        if user not in self.info:
            return

        self.log_warning(_("Account `%s` is expired") % user, _("Checking again in 60 minutes"))

        self.info[user]['data']['validuntil'] = time.time() - 1
        self.schedule_refresh(user, 60 * 60)


    def schedule_refresh(self, user, time=0, reload=True):
        """
        Add task to refresh account info to sheduler
        """
        self.log_debug("Scheduled refresh for user `%s` in %s seconds" % (user, time))
        self.pyload.scheduler.addJob(time, self.get_info, [user, reload])


    #: Deprecated method, use `schedule_refresh` instead (Remove in 0.4.10)
    def scheduleRefresh(self, *args, **kwargs):
        if 'force' in kwargs:
            kwargs.pop('force', None)  #@TODO: Recheck in 0.4.10
        return self.schedule_refresh(*args, **kwargs)


    @lock
    def is_logged(self, user, relogin=False):
        """
        Checks if user is still logged in
        """
        if user in self.info:
            if self.LOGIN_TIMEOUT > 0 and self.info[user]['login']['timestamp'] + self.LOGIN_TIMEOUT < time.time():
                self.log_debug("Reached login timeout for %s" % user)
                return self.relogin(user) if relogin else False
            else:
                return True
        else:
            return False
