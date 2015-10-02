# -*- coding: utf-8 -*-

import random
import time
import threading

from module.plugins.Plugin import SkipDownload as Skip
from module.plugins.internal.Plugin import Plugin, parse_size
from module.utils import compare_time, lock


class Account(Plugin):
    __name__    = "Account"
    __type__    = "account"
    __version__ = "0.53"
    __status__  = "testing"

    __description__ = """Base account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    LOGIN_TIMEOUT = 10 * 60  #: Relogin accounts every 10 minutes
    AUTO_TIMEOUT  = True     #: Automatically adjust relogin interval


    def __init__(self, manager, accounts):
        self._init(manager.core)

        self.manager = manager
        self.lock    = threading.RLock()

        self.accounts = accounts  #@TODO: Recheck in 0.4.10
        self.user     = None

        self.interval     = self.LOGIN_TIMEOUT
        self.auto_timeout = self.interval if self.AUTO_TIMEOUT else False

        self.init()


    def init(self):
        """
        Initialize additional data structures
        """
        pass


    @property
    def logged(self):
        """
        Checks if user is still logged in
        """
        if not self.user:
            return False

        self.sync()

        if self.info['login']['timestamp'] + self.interval < time.time():
            self.log_debug("Reached login timeout for user `%s`" % self.user)
            return False
        else:
            return True


    @property
    def premium(self):
        return bool(self.get_data('premium'))


    def signin(self, user, password, data):
        """
        Login into account, the cookies will be saved so user can be recognized
        """
        pass


    def login(self):
        if not self.req:
            self.log_info(_("Login user `%s`...") % self.user)
        else:
            self.log_info(_("Relogin user `%s`...") % self.user)
            self.clean()

        self.req = self.pyload.requestFactory.getRequest(self.__name__, self.user)

        self.sync()

        try:
            self.info['login']['timestamp'] = time.time()  #: Set timestamp for login
            self.signin(self.user, self.info['login']['password'], self.info['data'])

        except Skip:
            self.info['login']['valid'] = True
            if self.auto_timeout:
                self.auto_timeout *= 2
                self.interval = self.auto_timeout

        except Exception, e:
            self.log_error(_("Could not login user `%s`") % user, e)
            self.info['login']['valid'] = False

        else:
            self.info['login']['valid'] = True
            if self.interval is self.auto_timeout:
                self.interval = self.auto_timeout / 2
                self.auto_timeout = False

        finally:
            self.syncback()
            return bool(self.info['login']['valid'])


    #@TODO: Recheck in 0.4.10
    def syncback(self):
        return self.sync(reverse=True)


    #@TODO: Recheck in 0.4.10
    def sync(self, reverse=False):
        if not self.user:
            return

        u = self.accounts[self.user]

        if reverse:
            u.update(self.info['data'])
            u.update(self.info['login'])

        else:
            d = {'login': {'password' : u['password'],
                           'timestamp': u['timestamp'],
                           'valid'    : u['valid']},
                 'data' : {'maxtraffic' : u['maxtraffic'],
                           'options'    : u['options'],
                           'premium'    : u['premium'],
                           'trafficleft': u['trafficleft'],
                           'validuntil' : u['validuntil']}}

            self.info.update(d)


    def relogin(self):
        return self.login()


    def reset(self):
        self.sync()

        d = {'maxtraffic' : None,
             'options'    : {'limitdl': ['0']},
             'premium'    : None,
             'trafficleft': None,
             'validuntil' : None}

        self.info['data'].update(d)

        self.syncback()


    def get_info(self, refresh=True):
        """
        Retrieve account infos for an user, do **not** overwrite this method!
        just use it to retrieve infos in hoster plugins. see `grab_info`

        :param user: username
        :param relogin: reloads cached account information
        :return: dictionary with information
        """
        if not self.logged:
            if self.relogin():
                refresh = True
            else:
                refresh = False
                self.reset()

        if refresh:
            self.log_info(_("Grabbing account info for user `%s`...") % self.user)
            self.info = self._grab_info()

            self.syncback()

            safe_info = dict(self.info)
            safe_info['login']['password'] = "**********"
            self.log_debug("Account info for user `%s`: %s" % (self.user, safe_info))

        return self.info


    def get_login(self, key=None, default=None):
        d = self.get_info()['login']
        return d.get(key, default) if key else d


    def get_data(self, key=None, default=None):
        d = self.get_info()['data']
        return d.get(key, default) if key else d


    def _grab_info(self):
        try:
            data = self.grab_info(self.user, self.info['login']['password'], self.info['data'])

            if data and isinstance(data, dict):
                self.info['data'].update(data)

        except Exception, e:
            self.log_warning(_("Error loading info for user `%s`") % self.user, e)

        finally:
            return self.info


    def grab_info(self, user, password, data):
        """
        This should be overwritten in account plugin
        and retrieving account information for user

        :param user:
        :param req: `Request` instance
        :return:
        """
        pass


    ###########################################################################
    #@TODO: Recheck and move to `AccountManager` in 0.4.10 ####################
    ###########################################################################

    @lock
    def init_accounts(self):
        accounts = dict(self.accounts)
        self.accounts.clear()

        for user, info in accounts.items():
            self.add(user, info['password'], info['options'])


    @lock
    def getAccountData(self, user, force=False):
        self.accounts[user]['plugin'].get_info()
        return self.accounts[user]


    @lock
    def getAllAccounts(self, force=False):
        if force:
            self.init_accounts()  #@TODO: Recheck in 0.4.10

        return [self.getAccountData(user, force) for user in self.accounts]


    #@TODO: Remove in 0.4.10
    @lock
    def scheduleRefresh(self, user, force=False):
        pass


    @lock
    def add(self, user, password=None, options={}):
        self.log_info(_("Adding user `%s`...") % user)

        if user in self.accounts:
            self.log_error(_("Error adding user `%s`") % user, _("User already exists"))
            return False

        d = {'login'      : user,
             'maxtraffic' : None,
             'options'    : options or {'limitdl': ['0']},
             'password'   : password or "",
             'plugin'     : self.__class__(self.manager, self.accounts),
             'premium'    : None,
             'timestamp'  : 0,
             'trafficleft': None,
             'type'       : self.__name__,
             'valid'      : None,
             'validuntil' : None}

        u = self.accounts[user] = d
        return u['plugin'].choose(user)


    @lock
    def updateAccounts(self, user, password=None, options={}):
        """
        Updates account and return true if anything changed
        """
        if user in self.accounts:
            self.log_info(_("Updating account info for user `%s`...") % user)

            u = self.accounts[user]
            if password:
                u['password'] = password

            if options:
                u['options'].update(options)

            u['plugin'].relogin()

        else:
            self.add(user, password, options)


    @lock
    def removeAccount(self, user):
        self.log_info(_("Removing user `%s`...") % user)
        self.accounts.pop(user, None)
        if user is self.user:
            self.choose()


    @lock
    def select(self):
        free_accounts    = {}
        premium_accounts = {}

        for user in self.accounts:
            info = self.accounts[user]['plugin'].get_info()
            data = info['data']

            if not info['login']['valid']:
                continue

            if data['options'].get('time'):
                time_data = ""
                try:
                    time_data  = data['options']['time'][0]
                    start, end = time_data.split("-")

                    if not compare_time(start.split(":"), end.split(":")):
                        continue

                except Exception:
                    self.log_warning(_("Invalid time format `%s` for account `%s`, use 1:22-3:44")
                                     % (user, time_data))

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

        validuntil_list = [(user, info) for user, info in account_list \
                           if info['data']['validuntil']]

        if not validuntil_list:
            return random.choice(account_list)  #@TODO: Random account?! Rewrite in 0.4.10

        return sorted(validuntil_list,
                      key=lambda a: a[1]['data']['validuntil'],
                      reverse=True)[0]


    @lock
    def choose(self, user=None):
        """
        Choose a valid account
        """
        if not user:
            user = self.select()[0]

        elif user not in self.accounts:
            self.log_error(_("Error choosing user `%s`") % user, _("User not exists"))
            return False

        if user is self.user:
            return True

        self.user = user
        self.info.clear()
        self.clean()

        if self.user is not None:
            self.login()
            return True

        else:
            return False


    ###########################################################################

    def parse_traffic(self, size, unit="KB"):  #@NOTE: Returns kilobytes in 0.4.9
        size = re.search(r'(\d*[\.,]?\d+)', size).group(1)  #@TODO: Recjeck in 0.4.10
        return parse_size(size, unit) / 1024  #@TODO: Remove `/ 1024` in 0.4.10


    def fail_login(self, msg=_("Login handshake has failed")):
        return self.fail(msg)


    def skip_login(self, msg=_("Already signed in")):
        return self.skip(msg)
