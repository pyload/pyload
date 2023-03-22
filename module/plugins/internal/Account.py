# -*- coding: utf-8 -*-

import copy
import threading
import time

from .misc import Periodical, compare_time, decode, isiterable, lock, parse_size
from .Plugin import Plugin, Skip


class Account(Plugin):
    __name__ = "Account"
    __type__ = "account"
    __version__ = "0.90"
    __status__ = "stable"

    __description__ = """Base account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    #: Relogin account every 30 minutes, use -1 for never expire, you have to explicitly call relogin() when needed
    LOGIN_TIMEOUT = 30 * 60
    TUNE_TIMEOUT = True     #: Automatically tune relogin interval

    def __init__(self, manager, accounts):
        self._init(manager.core)

        self.manager = manager
        self.lock = threading.RLock()

        self.accounts = accounts  # @TODO: Recheck in 0.4.10
        self.user = None

        self.timeout = self.LOGIN_TIMEOUT

        #: Callback of periodical job task, used by HookManager
        self.periodical = Periodical(self, self.periodical_task)
        self.cb = self.periodical.cb  # @TODO: Recheck in 0.4.10

        self.init()

    @property
    def logged(self):
        """
        Checks if user is still logged in
        """
        if not self.user:
            return False

        self.sync()

        if self.info['login']['timestamp'] == 0 or \
                                self.timeout != -1 and self.info['login']['timestamp'] + self.timeout < time.time():
            self.log_debug("Reached login timeout for user `%s`" % self.user)
            return False
        else:
            return True

    @property
    def premium(self):
        return bool(self.get_data('premium'))

    def _log(self, level, plugintype, pluginname, messages, tbframe=None):
        msg = u" | ".join(decode(a).strip() for a in messages if a)

        #: Hide any user/password
        try:
            msg = msg.replace(self.user, self.user[:3] + "*******")
        except Exception:
            pass

        try:
            msg = msg.replace(self.info['login']['password'], "**********")
        except Exception:
            pass

        return Plugin._log(self, level, plugintype, pluginname, (msg, ), tbframe=tbframe)

    def setup(self):
        """
        Setup for environment and other things, called before logging (possibly more than one time)
        """
        pass

    def periodical_task(self):
        raise NotImplementedError

    def signin(self, user, password, data):
        """
        Login into account, the cookies will be saved so user can be recognized
        """
        pass

    def login(self):
        self.clean()
        self.sync()

        self.info["login"]["stats"][0] += 1
        if self.info["login"]["stats"][0] == 1:
            self.log_info(_("Login user `%s`...") % self.user)
        else:
            self.log_info(_("Relogin user `%s`...") % self.user)

        self.req = self.pyload.requestFactory.getRequest(
            self.classname, self.user)

        self.setup()

        timestamp = time.time()

        try:
            self.signin(
                self.user,
                self.info['login']['password'],
                self.info['data'])

        except Skip, e:
            self.log_warning(_("Skipped login user `%s`") % self.user, e)
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
            #: Set timestamp for login
            self.info['login']['timestamp'] = timestamp

            self.syncback()

            return bool(self.info['login']['valid'])


    def logout(self):
        """
        Invalidate the account timestamp so relogin will be forced next time.
        """
        self.sync()
        self.info["login"]["timestamp"] = 0
        self.syncback()

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
            d = {'login': {}, 'data': {}}

            for k, v in u.items():
                if k in ('password', 'timestamp', "stats", 'valid'):
                    d['login'][k] = v
                else:
                    d['data'][k] = v

            self.info.update(d)

    def relogin(self):
        return self.login()

    def reset(self):
        self.sync()

        clear = lambda x: {} if isinstance(
            x, dict) else [] if isiterable(x) else None
        self.info['data'] = dict((k, clear(v))
                                 for k, v in self.info['data'].items())
        self.info['data']['options'] = {'limitDL': ['0']}

        self.syncback()

    def get_info(self, refresh=True):
        """
        Retrieve account infos for an user, do **not** overwrite this method!
        just use it to retrieve infos in hoster plugins. see `grab_info`

        :return: dictionary with information
        """
        if not self.logged:
            if self.relogin():
                refresh = True
            else:
                refresh = False
                self.reset()

        if refresh and self.info['login']['valid']:
            self.log_info(
                _("Grabbing account info for user `%s`...") %
                self.user)
            self.info = self._grab_info()

            self.syncback()

            self.log_debug(
                "Account info for user `%s`: %s" %
                (self.user, self.info))

        return self.info

    def get_login(self, key=None, default=None):
        d = self.get_info()['login']
        return d.get(key, default) if key else d

    def get_data(self, key=None, default=None):
        d = self.get_info()['data']
        return d.get(key, default) if key else d

    def _grab_info(self):
        try:
            data = self.grab_info(
                self.user,
                self.info['login']['password'],
                self.info['data'])

            if data and isinstance(data, dict):
                self.info['data'].update(data)

        except Exception, e:
            self.log_warning(
                _("Error loading info for user `%s`") %
                self.user, e)

        finally:
            return self.info

    def grab_info(self, user, password, data):
        """
        This should be overwritten in account plugin
        and retrieving account information for user

        :param user:
        :param password:
        :param data:
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
            self.init_accounts()  # @TODO: Recheck in 0.4.10

        # @NOTE: `init_accounts()` already calls getAccountData(user, True), avoid calling `get_info()` twice
        # @NOTE: So force=False always here
        return [self.getAccountData(user, False) for user in self.accounts]

    #@TODO: Remove in 0.4.10
    @lock
    def scheduleRefresh(self, user, force=False):
        pass

    @lock
    def add(self, user, password=None, options={}):
        self.log_info(_("Adding user `%s`...") % (user[:3] + "*******"))

        if user in self.accounts:
            self.log_error(
                _("Error adding user `%s`") %
                user, _("User already exists"))
            return False

        d = {'login': user,
             'maxtraffic': None,
             'options': options or {'limitDL': ['0']},
             'password': password or "",
             'plugin': self.pyload.accountManager.getAccountPlugin(self.classname),
             'premium': None,
             "stats": [0, 0],  #: login_count, chosen_time
             'timestamp': 0,
             'trafficleft': None,
             'type': self.__name__,
             'valid': None,
             'validuntil': None}

        u = self.accounts[user] = d
        result = u['plugin'].choose(user)
        u['plugin'].get_info()

        return result

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
        # self.pyload.requestFactory.remove_cookie_jar(self.classname, user)
        self.pyload.requestFactory.cookiejars.pop((self.classname, user), None)
        if user is self.user:
            self.choose()

    @lock
    def select(self):
        def hide(secret):
            hidden = secret[:3] + "*******"
            return hidden

        free_accounts = {}
        premium_accounts = {}

        for user in self.accounts:
            if not self.accounts[user]["plugin"].choose(user):
                continue

            info = self.accounts[user]["plugin"].get_info()
            if not info['login']['valid']:
                continue

            data = info["data"]

            if data['options'].get('time'):
                time_data = ""
                try:
                    time_data = data['options']['time'][0]
                    start, end = time_data.split("-")

                    if not compare_time(start.split(":"), end.split(":")):
                        continue

                except Exception:
                    self.log_warning(_("Invalid time format `%s` for account `%s`, use 1:22-3:44")
                                     % (hide(user), time_data))

            if data['trafficleft'] == 0:
                self.log_warning(
                    _("Not using account `%s` because the account has no traffic left") %
                    hide(user))
                continue

            if time.time() > data['validuntil'] > 0:
                self.log_warning(
                    _("Not using account `%s` because the account has expired") %
                    hide(user))
                continue

            if data['premium']:
                premium_accounts[user] = copy.copy(info)

            else:
                free_accounts[user] = copy.copy(info)

        account_list = (premium_accounts or free_accounts).items()

        if not account_list:
            return None, None

        #: Choose the oldest used account
        chosen_account = sorted(account_list, key=lambda x: x[1]["login"]["stats"][1])[0]
        self.accounts[chosen_account[0]]["stats"][1] = time.time()

        self.log_debug("Using account %s" % (hide(chosen_account[0])))
        return chosen_account

    @lock
    def choose(self, user=None):
        """
        Choose a valid account
        """
        if not user:
            user = self.select()[0]

        elif user not in self.accounts:
            self.log_error(
                _("Error choosing user `%s`") %
                user, _("User does not exists"))
            return False

        else:
            if self.req and user == self.user:
                return True

        if user is None:
            return False

        else:
            self.user = user
            self.info.clear()
            self.req.close()
            self.req = self.pyload.requestFactory.getRequest(self.classname, self.user)

            if not self.logged:
                self.relogin()

            return True

    ###########################################################################

    def parse_traffic(self, size, unit=None):  #: returns bytes
        self.log_debug("Size: %s" % size,
                       "Unit: %s" % (unit or "N/D"))
        return parse_size(size, unit or "byte")

    def fail_login(self, msg=_("Login handshake has failed")):
        return self.fail(msg)

    def skip_login(self, msg=_("Already signed in")):
        return self.skip(msg)
