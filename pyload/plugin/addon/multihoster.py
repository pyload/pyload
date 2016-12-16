# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re
from random import choice

from pyload.plugin.multihoster import MultiHoster as MultiHosterAccount, normalize
from pyload.plugin.addon import Addon, add_event_listener
from pyload.manager.pluginmanager import PluginMatcher


class MultiHoster(Addon, PluginMatcher):
    __version__ = "0.1"
    __internal__ = True
    __description__ = "Gives ability to use MultiHoster services."
    __config__ = []
    __author__ = ("pyLoad Team",)
    __author_mail__ = ("support@pyload.net",)

    #TODO: multiple accounts - multihoster / config options

    def init(self):
        # overwritten plugins mapped to list of multihoster
        self.plugins = {}

        # multihoster mapped to new regexp
        self.regexp = {}

    def match_url(self, url):
        """ Overwritten to include new plugin regexp """
        for hoster, regexp in self.regexp.items():
            if regexp.search(url):
                return "hoster", hoster

    def match_plugin(self, plugin, name):
        """ Overwritten to overwrite already supported plugins """

        # TODO: check if account is usable
        # TODO: multiuser

        # Chooses a random multi hoster plugin
        if name in self.plugins:
            return plugin, choice(self.plugins[name])

    def add_hoster(self, account):

        self.log_info(_("Activated %s") % account.__name__)

        pluginMap = {}
        for name in self.pyload.pluginmanager.get_plugins("hoster").keys():
            pluginMap[name.lower()] = name

        supported = []
        new_supported = []

        for hoster in account.getHosterList():
            name = normalize(hoster)

            if name in pluginMap:
                supported.append(pluginMap[name])
            else:
                new_supported.append(hoster)

        if not supported and not new_supported:
            account.log_error(_("No Hoster loaded"))
            return

        klass = self.pyload.pluginmanager.get_plugin_class("hoster", account.__name__, overwrite=False)

        if not klass:
            return

        # inject plugin plugin
        account.log_debug("Overwritten Hosters: %s" % ", ".join(sorted(supported)))
        for hoster in supported:
            if hoster in self.plugins:
                self.plugins[hoster].append(klass.__name__)
            else:
                self.plugins[hoster] = [klass.__name__]

        account.log_debug("New Hosters: %s" % ", ".join(sorted(new_supported)))

        # create new regexp
        patterns = [x.replace(".", "\\.") for x in new_supported]

        if klass.__pattern__:
            patterns.append(klass.__pattern__)

        self.regexp[klass.__name__] = re.compile(r".*(%s).*" % "|".join(patterns))


    @add_event_listener(["account:deleted", "account:updated"])
    def refresh_accounts(self, plugin=None, loginname=None, user=None):
        self.log_debug("Re-checking accounts")

        self.plugins = {}
        for plugin, account in self.pyload.accountmanager.iter_accounts():
            if isinstance(account, MultiHosterAccount) and account.is_usable():
                self.add_hoster(account)

    @add_event_listener("account:loaded")
    def refresh_account(self, acc):

        account = self.pyload.accountmanager.get_account(acc.plugin, acc.loginname)
        if isinstance(account, MultiHosterAccount) and account.is_usable():
            self.add_hoster(account)

    def activate(self):
        self.refresh_accounts()
        self.pyload.pluginmanager.add_matcher(self)

    def deactivate(self):
        self.pyload.pluginmanager.remove_matcher(self)
