# -*- coding: utf-8 -*-

import random
import re
import time
import threading

from module.plugins.Plugin import SkipDownload as Skip
from module.plugins.internal.Plugin import Plugin, parse_size
from module.utils import compare_time, lock


class Account(Plugin):
    __name__    = "Account"
    __type__    = "account"
    __version__ = "0.62"
    __status__  = "testing"

    __description__ = """Base account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    LOGIN_TIMEOUT = 30 * 60  #: Relogin account every 30 minutes
    TUNE_TIMEOUT  = True     #: Automatically tune relogin interval

    PERIODICAL_INTERVAL = None


    def __init__(self, manager, accounts):
        self._init(manager.core)

        self.manager = manager
        self.lock    = threading.RLock()

        self.accounts = accounts  #@TODO: Recheck in 0.4.10
        self.user     = None

        self.timeout = self.LOGIN_TIMEOUT

        #: Callback of periodical job task
        self.cb       = None
        self.interval = self.PERIODICAL_INTERVAL

        self.init()


    def init(self):
        """
        Initialize additional data structures
        """
        pass


    def set_interval(self, value):
        newinterval = max(0, self.PERIODICAL_INTERVAL, value)

        if newinterval != value:
            return False

        if newinterval != self.interval:
            self.interval = newinterval

        return True


    def start_periodical(self, interval=None, threaded=False, delay=None):
        if interval is not None and self.set_interval(interval) is False:
            return False
        else:
            self.cb = self.pyload.scheduler.addJob(max(1, delay), self._periodical, [threaded], threaded=threaded)
            return True


    def restart_periodical(self, *args, **kwargs):
        self.stop_periodical()
        return self.start_periodical(*args, **kwargs)


    def stop_periodical(self):
        try:
            return self.pyload.scheduler.removeJob(self.cb)
        finally:
            self.cb = None


    def _periodical(self, threaded):
        try:
            self.periodical()

        except Exception, e:
            self.log_error(_("Error executing periodical task: %s") % e, trace=True)

        self.restart_periodical(threaded=threaded, delay=self.interval)


    def periodical(self):
        raise NotImplementedError


    @property
    def logged(self):
        """
        Checks if user is still logged in
        """
        if not self.user:
            return False

        self.sync()

        if self.info['login']['timestamp'] + self.timeout < time.time():
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

        self.req = self.pyload.requestFactory.getRequest(self.classname, self.user)

        self.sync()

        timestamp = time.time()

        try:
            self.signin(self.user, self.info['login']['password'], self.info['data'])

        except Skip, e:
            self.log_debug(e)
            self.info['login']['valid'] = True

            new_timeout = timestamp - self.info['login']['timestamp']
            if self.TUNE_TIMEOUT and new_timeout > self.timeout:
                self.timeout = new_timeout

        except Exception, e:
            self.log_error(_("Could not login user `%s`") % self.user, e)
            self.info['login']['valid'] = False

        else:
            self.info['login']['valid'] = True

        finally:
            self.info['login']['timestamp'] = timestamp  #: Set timestamp for login

            self.syncback()

            return bool(self.info['login']['valid'])


    #@TODO: Recheck in 0.4.10
    def syncback(self):
        """
        Wrapper to directly sync self.info -> self.accounts[self.user]
        """
        return self.sync(reverse=True)


    #@TODO: Recheck in 0.4.10
    def sync(self, reverse=False):
        """
        Sync self.accounts[self.user] -> self.info
        or self.info -> self.accounts[self.user] (if reverse is True)
        """
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
        if force:
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

        if self.req and user is self.user:
            return True

        self.user = user
        self.info.clear()
        self.clean()

        if user is None:
            return False

        else:
            if not self.logged:
                self.relogin()
            else:
                self.req = self.pyload.requestFactory.getRequest(self.classname, self.user)

            return True


    ###########################################################################

    def parse_traffic(self, size, unit="byte"):  #@NOTE: Returns kilobytes in 0.4.9
        unit = unit.lower().strip()  #@TODO: Remove in 0.4.10
        size = re.search(r'(\d*[\.,]?\d+)', size).group(1)  #@TODO: Recheck in 0.4.10

        self.log_debug("Size: %s" % size, "Unit: %s" % unit)

        #@NOTE: Remove in 0.4.10
        if unit.startswith('t'):
            traffic = float(size.replace(',', '.')) * 1 << 40
        else:
            traffic = parse_size(size, unit)

        return traffic / 1024  #@TODO: Remove `/ 1024` in 0.4.10


    def fail_login(self, msg=_("Login handshake has failed")):
        return self.fail(msg)


    def skip_login(self, msg=_("Already signed in")):
        return self.skip(msg)
